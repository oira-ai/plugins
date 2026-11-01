"""Bounded lifecycle checkpoints. This module never imports network/credentials."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import sqlite3
import shlex
import hashlib
import marshal
import sys
import time
from uuid import UUID
from datetime import datetime
from contextlib import closing
from types import CodeType

try:
    from .local import (
        Store,
        LocalError,
        binding_key,
        canonical,
        repository as repository,
        resolve_binding,
        resolve_binding_key,
        stable_target,
        validate_target,
    )
except ImportError:
    from oira_local import (
        Store,
        LocalError,
        binding_key,
        canonical,
        resolve_binding,
        resolve_binding_key,
        stable_target,
        validate_target,
    )

MAX_INPUT = 1024 * 1024
HOOK_EVENTS = ('SessionStart', 'UserPromptSubmit', 'Stop')


def _binding_digest(project):
    target = validate_target(project.get('expected_target'))
    if target is None:
        raise LocalError('binding_repair_required')
    return hashlib.sha256(canonical({
        'expected_target': target, 'transport': project.get('transport', 'native_oauth'),
        'installation': project.get('installation'),
    }).encode()).hexdigest()


def _code_identity(code):
    # Native hosts copy the same package into a cache. Absolute source paths are
    # not implementation changes, including in nested comprehensions/lambdas.
    def constant(item):
        if isinstance(item, CodeType):
            return _code_identity(item)
        if isinstance(item, frozenset):
            # Compiler-folded `in {…}` constants must not vary by hash seed
            # between hook processes or a copied native plugin cache.
            return ('<frozenset>', tuple(sorted((constant(value) for value in item), key=repr)))
        if isinstance(item, tuple):
            return tuple(constant(value) for value in item)
        return item
    return code.replace(co_filename='<oira-hooks>', co_consts=tuple(map(constant, code.co_consts)))


def _helper_digest():
    # Works for source packages and frozen launchers without reading credentials
    # or assuming that a .py file was extracted beside the executable.
    functions = (_code_identity, _binding_digest, _verification, verification_projection, begin_verification,
                 observe_hook, verification_status, finish_verification, reminder, event,
                 Store._session_identity, Store.session_policy, Store.observe_session)
    # Format 0 avoids runtime-dependent interned-string/reference flags.
    return hashlib.sha256(marshal.dumps((HOOK_EVENTS, *(_code_identity(function.__code__) for function in functions)), 0)).hexdigest()


def _verification(project, check_ref):
    value = project.get('setup_verification', {})
    return value if (isinstance(value, dict) and isinstance(value.get('sessions'), dict)
                     and value.get('check_ref') == check_ref
                     and value.get('helper_digest') == _helper_digest()
                     and value.get('binding_digest') == _binding_digest(project)) else None


def verification_projection(project, check_ref, session=None, *, db):
    value = _verification(project, check_ref)
    sessions = value.get('sessions', {}) if value else {}
    observations = {identity: {name: {key: item[key] for key in ('observed_at', 'nonce')}
                              for name, item in events.items() if name in HOOK_EVENTS
                              and isinstance(item, dict) and isinstance(item.get('observed_at'), (int, float))
                              and isinstance(item.get('nonce'), str)}
                    for identity, events in sessions.items() if isinstance(events, dict)
                    and (session is None or identity == session)}
    observed = False
    for identity, events in observations.items():
        turn = db.execute('SELECT nonce,destination FROM turns WHERE session=?', (identity,)).fetchone()
        if (set(events) == set(HOOK_EVENTS) and turn is not None
                and turn[0] == events['UserPromptSubmit']['nonce'] == events['Stop']['nonce']
                and turn[1] == stable_target(project['expected_target'])
                and value['started_at'] <= events['SessionStart']['observed_at']
                <= events['UserPromptSubmit']['observed_at'] <= events['Stop']['observed_at']):
            observed = True
            break
    enabled = project.get('enabled', True)
    stored_ack = value.get('setup_ack') if value else None
    ack = ({'accepted_at': stored_ack['accepted_at'], 'provenance': 'host_reported'}
           if isinstance(stored_ack, dict) and isinstance(stored_ack.get('accepted_at'), str)
           and stored_ack.get('provenance') == 'host_reported' else None)
    return {
        'schema': 'oira_hook_verification.v1', 'check_ref': check_ref,
        'state': 'complete' if enabled and value and value.get('complete') is True and ack else
                 'hooks_observed' if enabled and observed else 'waiting_for_hooks' if value and enabled else 'not_started',
        'automatic_reporting': 'enabled' if enabled else 'disabled',
        'review_confirmed': bool(value and value.get('review_confirmed')),
        'native_trust': 'verify_in_host', 'evidence': 'local_observation_not_native_attestation',
        'native_send_permission': 'verify_in_host', 'work_capture': 'not_tested',
        'observations': observations, 'expected_target': project['expected_target'],
        'transport': project.get('transport', 'native_oauth'), 'installation': project.get('installation'),
        'setup_ack': ack,
    }


def begin_verification(store, root, check_ref, *, reviewed=False, session=None):
    if str(UUID(check_ref)) != check_ref:
        raise LocalError('invalid_check_ref')
    with store.transaction():
        projects = store.bindings()
        key = resolve_binding_key(projects, Path(root), session)
        project = projects.get(key)
        if not project or not project.get('enabled', True):
            raise LocalError('enabled_binding_required')
        value = _verification(project, check_ref)
        recorded = project.get('setup_verification')
        if value is None and isinstance(recorded, dict) and recorded.get('check_ref') == check_ref:
            # Changed helper/owner evidence must not reuse an old server receipt.
            raise LocalError('fresh_check_required')
        value = value or {
            'check_ref': check_ref, 'binding_digest': _binding_digest(project),
            'helper_digest': _helper_digest(),
            'started_at': time.time(), 'sessions': {}, 'stop_check_sessions': [],
        }
        value['review_confirmed'] = bool(value.get('review_confirmed') or reviewed)
        if reviewed and not value.get('complete'):
            # A deliberate user/native-review confirmation can rearm one final
            # check. Merely polling or a Stop continuation never rearms it.
            value['stop_check_sessions'] = [identity for identity in value.get('stop_check_sessions', [])
                                            if session is not None and identity != session]
        project['setup_verification'] = value
        store.db.execute('UPDATE bindings SET value=? WHERE key=?', (canonical(project), key))
        return verification_projection(project, check_ref, session, db=store.db)


def observe_hook(store, root, session, name, nonce, *, expected_binding):
    """Bounded technical observations only. Never retain a hook payload/body."""
    with store.transaction():
        projects = store.bindings()
        key = resolve_binding_key(projects, Path(root), session)
        project = projects.get(key)
        turn = store.db.execute('SELECT nonce,destination FROM turns WHERE session=?', (session,)).fetchone()
        if (not project or not project.get('enabled', True)
                or _binding_digest(project) != _binding_digest(expected_binding)
                or turn is None or turn[0] != nonce
                or turn[1] != stable_target(project['expected_target'])):
            return False, None
        recorded = project.get('setup_verification')
        check_ref = recorded.get('check_ref') if isinstance(recorded, dict) else None
        value = _verification(project, check_ref) if check_ref else None
        prior = expected_binding.get('setup_verification')
        if (not value or value.get('complete') or not isinstance(prior, dict)
                or prior.get('check_ref') != check_ref):
            return True, None
        sessions = value['sessions']
        if name == 'SessionStart':
            # A native reload must not combine its new start with an old turn.
            sessions[session] = {}
        events = sessions.setdefault(session, {})
        if name == 'UserPromptSubmit':
            events.pop('Stop', None)
        events[name] = {'observed_at': time.time(), 'nonce': nonce}
        if len(sessions) > 4:
            oldest = min((identity for identity in sessions if identity != session),
                         key=lambda identity: max(item['observed_at'] for item in sessions[identity].values()))
            del sessions[oldest]
        requested = value.setdefault('stop_check_sessions', [])
        request_final = name == 'Stop' and value.get('review_confirmed') and session not in requested
        if request_final:
            value['stop_check_sessions'] = [*requested, session][-4:]
        store.db.execute('UPDATE bindings SET value=? WHERE key=?', (canonical(project), key))
        return True, check_ref if request_final else None


def verification_status(folder, root, check_ref, session=None):
    """Read existing state without creating/migrating it or simulating a hook."""
    if str(UUID(check_ref)) != check_ref:
        raise LocalError('invalid_check_ref')
    path = folder / 'state.sqlite3'
    if not path.exists():
        return {'schema': 'oira_hook_verification.v1', 'check_ref': check_ref, 'state': 'not_configured'}
    if path.is_symlink():
        raise LocalError('unsafe_state_path')
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=2)) as db:
        db.execute('BEGIN')  # One read-only snapshot for bindings and current turns.
        projects = {key: json.loads(value) for key, value in db.execute('SELECT key,value FROM bindings')}
        project = resolve_binding(projects, Path(root), session)
        return (verification_projection(project, check_ref, session, db=db) if project else
                {'schema': 'oira_hook_verification.v1', 'check_ref': check_ref, 'state': 'not_configured'})


def finish_verification(store, root, check_ref, session, receipt):
    """Retain acknowledgment metadata as host-reported, never server-attested."""
    if str(UUID(check_ref)) != check_ref:
        raise LocalError('invalid_check_ref')
    if not isinstance(session, str) or not session:
        raise LocalError('session_required')
    with store.transaction():
        projects = store.bindings()
        key = resolve_binding_key(projects, Path(root), session)
        project = projects.get(key)
        if not project:
            raise LocalError('enabled_binding_required')
        state = verification_projection(project, check_ref, session, db=store.db)
        if state['state'] not in {'hooks_observed', 'complete'} or not state['review_confirmed']:
            raise LocalError('hook_verification_pending')
        if (not isinstance(receipt, dict) or receipt.get('schema') != 'oira_setup_check.v1'
                or receipt.get('result') != 'accepted' or receipt.get('check_ref') != check_ref
                or receipt.get('expected_target') != project['expected_target']
                or receipt.get('work_update_created') is not False
                or not isinstance(receipt.get('accepted_at'), str) or len(receipt['accepted_at']) > 64):
            raise LocalError('setup_ack_required')
        if datetime.fromisoformat(receipt['accepted_at'].replace('Z', '+00:00')).tzinfo is None:
            raise LocalError('setup_ack_required')
        value = project['setup_verification']
        value['complete'] = True
        value['setup_ack'] = {'accepted_at': receipt['accepted_at'], 'provenance': 'host_reported'}
        store.db.execute('UPDATE bindings SET value=? WHERE key=?', (canonical(project), key))
        return verification_projection(project, check_ref, session, db=store.db)


def data_dir(app, environment):
    return Path.home() / ".oira/reporting" / environment / app


def session_status(folder, session):
    """Read exclusions without creating state or running a schema migration."""
    identity = Store._session_identity(session)
    path = folder / 'state.sqlite3'
    row = None
    if path.is_symlink():
        raise LocalError('unsafe_state_path')
    if path.exists():
        with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=2)) as db:
            db.execute('BEGIN')
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='session_lifecycle'").fetchone():
                row = db.execute('SELECT purpose,first_event,native_start_seen FROM session_lifecycle WHERE identity=?', (identity,)).fetchone()
    return {'schema': 'oira_local_session_policy.v1', 'work_reporting': 'excluded' if row and row[0] == 'setup' else 'eligible',
            'first_observed_event': row[1] if row else None, 'native_start_seen': bool(row and row[2])}


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
    lifecycle=None,
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
        "Oira automatic reporting is configured for this exact binding. Follow the installed oira-work-reporting skill. "
        "Setup/verification chats are excluded: never report installation activity or import those chats. "
        "Report concise useful facts: what changed and why, a decision and its reason, checks and results, "
        "and remaining actions. At final handoff include the actual outcome; bookkeeping is not work progress. "
        + ("This working chat was first observed midrun (" + lifecycle['first_event'] + "). "
           "Before results, declare the actual work identity and context in the first structured update; include "
           "known progress, then results in causal order in that same update. Do not send an empty synthetic start, "
           "invent prior work/timestamps, or read transcripts. Recover existing stream/receipts before retrying. "
           if lifecycle and lifecycle.get('first_event') not in (None, 'SessionStart') else "")
        +
        "Native approval to disclose work is separate: this reminder and the binding do not override it. "
        "If confirmation is required, ask once with the exact destination and actual facts before sending. "
        "On an approval denial, stop reporting, explain it and wait for human approval; never reword, "
        "minimize or switch tools to bypass it. A setup acknowledgment is not a real work receipt. "
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
        policy = store.session_policy(session)
        excluded = policy is not None and policy['purpose'] == 'setup'
        project = resolve_binding(store.bindings(), Path(cwd), session)
        if not isinstance(project, dict) or not project.get("enabled", True):
            return {}
        target, label = (
            validate_target(project.get("expected_target")),
            project.get("project_label"),
        )
        if target is None or not isinstance(label, str) or not label.strip():
            return {}
        policy = store.observe_session(session, event=name)
        if excluded:
            pending = project.get('setup_verification')
            if (not isinstance(pending, dict) or pending.get('complete')
                    or not _verification(project, pending.get('check_ref'))):
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
        if name == 'Stop' and payload.get('stop_hook_active') is not False:
            return {}
        current, check_ref = observe_hook(store, cwd, session, name, turn['nonce'], expected_binding=project)
        if not current:
            return {}
        if excluded:
            # Local diagnostic evidence is allowed; ordinary work reminders and
            # sends are not. A missing pre-install start remains missing.
            if check_ref:
                return {'decision': 'block', 'reason': (
                    'Oira setup-only hook check. This chat is permanently excluded from work reporting; '
                    'never submit a work update or read/import this setup chat. The real Stop hook ran. '
                    'Read verify-status --project-root ' + shlex.quote(cwd) + ' --check-ref ' + check_ref
                    + ' --session-id ' + shlex.quote(session) + '. Follow references/setup-verification.md. '
                    'If SessionStart is missing because installation happened midrun, give one excluded '
                    'verification-chat continuation; do not fabricate events, report setup as work, or loop.'
                )}
            return {}
        if name == "Stop":
            if check_ref:
                return {'decision': 'block', 'reason': (
                    'Oira setup final hook check: the Stop hook just ran. Follow the installed setup-verification reference. '
                    'Run the same helper verify-status --project-root <this folder> --check-ref ' + check_ref
                    + ' --session-id ' + shlex.quote(session) + '. Confirm native hook review and all three fresh events '
                    'in this session before calling oira_verify_setup with this check_ref and the exact target. '
                    'If an event is missing, explain the pending reload/check once; do not fabricate it or loop. '
                    'Setup itself creates no work update. Complete the current checkpoint truthfully: '
                    'no_material_change for setup-only, or the normal skill/receipt path for genuine authorized work. '
                    + reminder(label, target, final=True, nonce=turn['nonce'], session=session,
                               checkpoint_command=checkpoint_command, transport=project.get('transport', 'native_oauth'),
                               installation=project.get('installation'))
                )}
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
                    lifecycle=policy,
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
                    lifecycle=policy,
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
    for name in ('exclude-session', 'session-status'):
        command = commands.add_parser(name)
        command.add_argument('--session-id', required=True)
    for name in ("bind", "enable", "disable"):
        command = commands.add_parser(name)
        command.add_argument("--project-root", required=True)
        command.add_argument("--session-id")
        command.add_argument("--inherit-repository", action="store_true")
        if name in {"bind", "enable"}:
            command.add_argument("--project-label", required=True)
            command.add_argument("--target-file", required=True)
            command.add_argument("--transport", choices=("native_oauth", "api_key"), default="native_oauth")
            command.add_argument("--installation")
    checkpoint = commands.add_parser("checkpoint")
    checkpoint.add_argument("--project-root", required=True)
    checkpoint.add_argument("--session-id", required=True)
    checkpoint.add_argument("--nonce", required=True)
    checkpoint.add_argument("--state", required=True)
    checkpoint.add_argument("--update-ref", action="append", default=[])
    for name in ('verify-begin', 'verify-status', 'verify-finish'):
        command = commands.add_parser(name)
        command.add_argument('--project-root', required=True)
        command.add_argument('--check-ref', required=True)
        command.add_argument('--session-id', required=name == 'verify-finish')
        if name == 'verify-begin':
            command.add_argument('--review-confirmed', action='store_true')
        if name == 'verify-finish':
            command.add_argument('--receipt-file', required=True)
    commands.add_parser("event")
    args = parser.parse_args(argv)
    folder = data_dir(args.app, args.environment)
    try:
        if args.command == 'verify-status':
            result = verification_status(folder, args.project_root, args.check_ref, args.session_id)
        elif args.command == 'session-status':
            result = session_status(folder, args.session_id)
        elif args.command == "event":
            raw = sys.stdin.buffer.read(MAX_INPUT + 1)
            payload = json.loads(raw) if len(raw) <= MAX_INPUT else None
            result = event(folder, payload) if isinstance(payload, dict) else {}
        else:
            store = Store(folder)
            try:
                if args.command == 'exclude-session':
                    store.observe_session(args.session_id, setup=True)
                    result = session_status(folder, args.session_id)
                    sys.stdout.buffer.write((json.dumps(result) + '\n').encode('utf-8'))
                    return 0
                if args.command == 'verify-begin':
                    result = begin_verification(store, args.project_root, args.check_ref,
                                                reviewed=args.review_confirmed, session=args.session_id)
                    sys.stdout.buffer.write((json.dumps(result) + '\n').encode('utf-8'))
                    return 0
                if args.command == 'verify-finish':
                    with Path(args.receipt_file).open('rb') as file:
                        raw = file.read(16 * 1024 + 1)
                    if len(raw) > 16 * 1024:
                        raise LocalError('setup_ack_too_large')
                    result = finish_verification(store, args.project_root, args.check_ref,
                                                 args.session_id, json.loads(raw))
                    sys.stdout.buffer.write((json.dumps(result) + '\n').encode('utf-8'))
                    return 0
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
                if args.command in {"bind", "enable"}:
                    if args.transport == "api_key":
                        if not args.installation or str(UUID(args.installation)) != args.installation:
                            raise ValueError("installation_required")
                    elif args.installation:
                        raise ValueError("unexpected_installation")
                    binding = store.bind(
                        key,
                        args.project_label,
                        json.loads(Path(args.target_file).read_text(encoding="utf-8")),
                        transport=args.transport,
                        installation=args.installation,
                        enabled=True if args.command == "enable" else None,
                    )
                else:
                    store.set_enabled(key, False)
                result = {"binding_saved": True, "automatic_reporting": "enabled" if binding["enabled"] else "disabled"} if args.command == "bind" else {
                    "automatic_reporting": "enabled" if args.command == "enable" else "disabled"
                }
            finally:
                store.close()
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
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
