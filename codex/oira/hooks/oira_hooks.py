"""Bounded lifecycle checkpoints. This module never imports network/credentials."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import sqlite3
import shlex
import hashlib
import sys

try:
    from .local import (
        Store,
        LocalError,
        binding_key,
        canonical,
        repository as repository,
        resolve_binding,
        validate_target,
    )
except ImportError:
    from oira_local import (
        Store,
        LocalError,
        binding_key,
        canonical,
        resolve_binding,
        validate_target,
    )

MAX_INPUT = 1024 * 1024


def data_dir(app, environment):
    return Path.home() / ".oira/reporting" / environment / app


def bindings(folder):
    if not folder.exists():
        return {}
    store = Store(folder)
    try:
        return store.bindings()
    finally:
        store.close()


def save_bindings(folder, projects):
    """Compatibility interface; SQLite is the sole active writer."""
    store = Store(folder)
    try:
        with store.transaction():
            store.db.execute("DELETE FROM bindings")
            for key, value in projects.items():
                store.db.execute(
                    "INSERT INTO bindings VALUES (?,?)",
                    (key, canonical(dict(value, enabled=value.get("enabled", True)))),
                )
    finally:
        store.close()


def reminder(
    label,
    target,
    *,
    final,
    nonce=None,
    session=None,
    app="codex",
    environment="production",
    checkpoint_command=None,
    transport="native_oauth",
    installation=None,
):
    owner = (
        "api_key installation " + str(installation)
        if transport == "api_key"
        else "native_oauth host tools"
    )
    command = (
        checkpoint_command
        + " --session-id "
        + shlex.quote(session)
        + " --nonce "
        + shlex.quote(nonce)
        if checkpoint_command
        else None
    )
    return (
        "Oira reporting is enabled for this exact binding. Follow the installed oira-work-reporting skill. "
        + "project_label (display data): "
        + json.dumps(label, ensure_ascii=True)
        + "; expected_target (data): "
        + canonical(target)
        + "; transport owner: "
        + owner
        + ". "
        + "Session: "
        + json.dumps(session)
        + "; nonce: "
        + json.dumps(nonce)
        + ". "
        + (
            "Final checkpoint command: "
            if final
            else "Before stopping, use checkpoint command: "
        )
        + str(command)
        + " --state <final-state> [--update-ref <captured-ref>]. "
        + "Use no_material_change, captured_finalized, blocked, unknown_send or repair_required. "
        + "This local command does not send work. Native receipts are host_reported."
    )


def event(folder, payload):
    name = payload.get("hook_event_name")
    if (
        name not in {"SessionStart", "UserPromptSubmit", "Stop"}
        or payload.get("agent_id")
        or payload.get("agent_type") not in (None, "", "main")
    ):
        return {}
    cwd, session = payload.get("cwd"), payload.get("session_id")
    if (
        not isinstance(cwd, str)
        or not isinstance(session, str)
        or not session
        or len(session) > 255
    ):
        return {}
    if not folder.exists():
        return {}
    store = Store(folder)
    try:
        project = resolve_binding(store.bindings(), Path(cwd), session)
        if not isinstance(project, dict) or not project.get("enabled", True):
            return {}
        target, label = (
            validate_target(project.get("expected_target")),
            project.get("project_label"),
        )
        if target is None or not isinstance(label, str) or not label.strip():
            return {}
        # No native turn-ID field is assumed. Duplicate registrations are a
        # diagnostic/qualification gate; explicit CLI begin IDs are separate.
        turn = store.turn(session, target, new=name == "UserPromptSubmit")
        launcher = store.db.execute(
            "SELECT value FROM meta WHERE key='launcher'"
        ).fetchone()
        if launcher and Path(launcher["value"]).is_file():
            checkpoint_command = (
                shlex.quote(launcher["value"])
                + " hook --app "
                + folder.name
                + " --environment "
                + folder.parent.name
                + " checkpoint --project-root "
                + shlex.quote(cwd)
            )
        else:
            helper = Path(__file__).parent / "reporting_hook.py"
            if not helper.is_file():
                helper = (
                    Path(__file__).resolve().parents[2]
                    / "shared/hooks/reporting_hook.py"
                )
            checkpoint_command = (
                shlex.quote(sys.executable)
                + " "
                + shlex.quote(str(helper))
                + " --app "
                + folder.name
                + " --environment "
                + folder.parent.name
                + " checkpoint --project-root "
                + shlex.quote(cwd)
            )
        if name == "Stop":
            if payload.get("stop_hook_active") is not False:
                return {}
            if not store.remind_once(session, turn["nonce"]):
                return {}
            return {
                "decision": "block",
                "reason": reminder(
                    label,
                    target,
                    final=True,
                    nonce=turn["nonce"],
                    session=session,
                    app=folder.name,
                    environment=folder.parent.name,
                    checkpoint_command=checkpoint_command,
                    transport=project.get("transport", "native_oauth"),
                    installation=project.get("installation"),
                ),
            }
        return {
            "hookSpecificOutput": {
                "hookEventName": name,
                "additionalContext": reminder(
                    label,
                    target,
                    final=False,
                    nonce=turn["nonce"],
                    session=session,
                    app=folder.name,
                    environment=folder.parent.name,
                    checkpoint_command=checkpoint_command,
                    transport=project.get("transport", "native_oauth"),
                    installation=project.get("installation"),
                ),
            }
        }
    except LocalError as exc:
        if exc.code in {
            "fresh_context_required",
            "retired_context_requires_fresh_session",
            "context_capacity_requires_repair",
        }:
            key = "fresh_context_notice:" + hashlib.sha256(session.encode()).hexdigest()
            result = store.db.execute(
                "INSERT OR IGNORE INTO meta VALUES (?,?)", (key, "shown")
            )
            if result.rowcount != 1:
                return {}
            return {
                "systemMessage": "Oira needs a fresh coding context or local-state repair. Run oira doctor before reporting to this target."
            }
        return {}
    finally:
        store.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", choices=("codex", "claude", "kiro"), required=True)
    parser.add_argument(
        "--environment", choices=("production", "development"), required=True
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("enable", "disable"):
        command = commands.add_parser(name)
        command.add_argument("--project-root", required=True)
        command.add_argument("--session-id")
        command.add_argument("--inherit-repository", action="store_true")
        if name == "enable":
            command.add_argument("--project-label", required=True)
            command.add_argument("--target-file", required=True)
    checkpoint = commands.add_parser("checkpoint")
    checkpoint.add_argument("--project-root", required=True)
    checkpoint.add_argument("--session-id", required=True)
    checkpoint.add_argument("--nonce", required=True)
    checkpoint.add_argument("--state", required=True)
    checkpoint.add_argument("--update-ref", action="append", default=[])
    commands.add_parser("event")
    args = parser.parse_args(argv)
    folder = data_dir(args.app, args.environment)
    try:
        if args.command == "event":
            raw = sys.stdin.buffer.read(MAX_INPUT + 1)
            payload = json.loads(raw) if len(raw) <= MAX_INPUT else None
            result = event(folder, payload) if isinstance(payload, dict) else {}
        else:
            store = Store(folder)
            try:
                if args.command == "checkpoint":
                    binding = resolve_binding(
                        store.bindings(), Path(args.project_root), args.session_id
                    )
                    if not binding:
                        raise LocalError("target_selection_required")
                    result = store.checkpoint(
                        args.session_id,
                        args.nonce,
                        binding["expected_target"],
                        args.state,
                        refs=args.update_ref,
                    )
                    sys.stdout.buffer.write((json.dumps(result) + "\n").encode("utf-8"))
                    return 0
                key = binding_key(
                    args.project_root,
                    session=args.session_id,
                    inherit=args.inherit_repository,
                )
                if args.command == "enable":
                    store.bind(
                        key,
                        args.project_label,
                        json.loads(Path(args.target_file).read_text(encoding="utf-8")),
                        enabled=True,
                    )
                else:
                    store.set_enabled(key, False)
                result = {
                    "automatic_reporting": "enabled"
                    if args.command == "enable"
                    else "disabled"
                }
            finally:
                store.close()
    except (
        OSError,
        ValueError,
        TypeError,
        UnicodeError,
        RecursionError,
        LocalError,
        sqlite3.Error,
    ):
        result = (
            {} if args.command == "event" else {"error": "configuration_unavailable"}
        )
    sys.stdout.buffer.write(
        (json.dumps(result, ensure_ascii=True) + "\n").encode("utf-8")
    )
    return 0 if "error" not in result else 1
