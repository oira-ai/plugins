"""Single local owner for exact bindings, turns and operational metadata.

Standard library only. Hooks import this module without importing transport or
credentials. No transcript, hook-body persistence, network or Git execution.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
from uuid import UUID, uuid4
from urllib.parse import urlsplit

TARGET_KEYS = {
    "schema",
    "environment",
    "user_uuid",
    "organization_uuid",
    "project_uuid",
    "connection_uuid",
    "resource_authority_uuid",
    "resource_epoch",
    "grant_uuid",
    "grant_generation",
    "mapping_revision",
}
EPOCH_KEYS = {"resource_epoch", "grant_generation", "mapping_revision"}
PENDING_DAYS = 7
MAX_PENDING = 1000
MAX_PENDING_BYTES = 32 * 1024 * 1024
MAX_METADATA = 10000
METADATA_DAYS = 30
CONTEXT_DAYS = 180
RETIRED_FILTER_BYTES = 1024 * 1024


class LocalError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def validate_target(target):
    if (
        not isinstance(target, dict)
        or set(target) != TARGET_KEYS
        or target.get("schema") != "oira_coding_target.v1"
    ):
        return None
    try:
        parts = urlsplit(target["environment"])
        if (
            parts.username
            or parts.password
            or parts.query
            or parts.fragment
            or not parts.hostname
            or not (
                parts.scheme == "https"
                or parts.scheme == "http"
                and parts.hostname in {"localhost", "127.0.0.1", "::1"}
            )
        ):
            return None
        parts.port
        for key in TARGET_KEYS:
            if key.endswith("_uuid") and str(UUID(target[key])) != target[key]:
                return None
        for key in EPOCH_KEYS:
            if type(target[key]) is not int or target[key] < 1:
                return None
    except (ValueError, TypeError, AttributeError):
        return None
    return target


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_target(target):
    if validate_target(target) is None:
        raise LocalError("invalid_target")
    return canonical(
        {key: value for key, value in target.items() if key not in EPOCH_KEYS}
    )


def repository(path):
    path = Path(path).resolve(strict=True)
    for parent in (path, *path.parents):
        marker = parent / ".git"
        if marker.is_dir():
            return str(marker.resolve())
        if marker.is_file():
            value = marker.read_text(encoding="utf-8").strip()
            if not value.startswith("gitdir: "):
                raise LocalError("invalid_git_marker")
            gitdir = (parent / value[8:]).resolve(strict=True)
            common = gitdir / "commondir"
            return str(
                (gitdir / common.read_text(encoding="utf-8").strip()).resolve(
                    strict=True
                )
                if common.is_file()
                else gitdir
            )
    return str(path)


def resolve_binding_key(projects, cwd, session):
    if session and "session:" + session in projects:
        return "session:" + session
    path = Path(cwd).resolve(strict=True)
    ancestors = (path, *path.parents)
    if not any((parent / ".git").exists() for parent in ancestors):
        key = "folder:" + str(path)
        return key if key in projects else None
    for parent in ancestors:
        key = "folder:" + str(parent)
        if key in projects:
            return key
        if (parent / ".git").exists():
            key = "repository:" + repository(parent)
            return key if key in projects else None
    return None


def resolve_binding(projects, cwd, session):
    return projects.get(resolve_binding_key(projects, cwd, session))


def binding_key(path, *, session=None, inherit=False):
    return (
        "session:" + session
        if session
        else "repository:" + repository(path)
        if inherit
        else "folder:" + str(Path(path).resolve(strict=True))
    )


def receipt_metadata(receipt):
    """Retain normalized returned identifiers, never a raw tool response."""
    allowed = ("work_ref", "work_handle", "fact_handles")
    works = []
    for work in receipt.get("works", [])[:32]:
        if isinstance(work, dict):
            works.append({key: work[key] for key in allowed if key in work})
    return {
        "capture": receipt.get("capture"),
        "update_ref": receipt.get("update_ref"),
        "update_digest": receipt.get("update_digest"),
        "sequence": receipt.get("sequence"),
        "works": works,
    }


class Store:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.lock_folder = (
            self.folder.parent.parent / "_locks"
            if self.folder.parent.name in {"production", "development"}
            else self.folder / "_locks"
        )
        self.folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.folder, 0o700)
        self.path = self.folder / "state.sqlite3"
        if self.path.is_symlink():
            raise LocalError("unsafe_state_path")
        self.db = sqlite3.connect(self.path, timeout=2, isolation_level=None)
        os.chmod(self.path, 0o600)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA secure_delete=ON")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS bindings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS contexts (session TEXT PRIMARY KEY, destination TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS turns (session TEXT PRIMARY KEY, destination TEXT NOT NULL,
            nonce TEXT NOT NULL, event_id TEXT, state TEXT NOT NULL, reminded INTEGER NOT NULL DEFAULT 0,
            provenance TEXT, refs TEXT, updated REAL NOT NULL);
          CREATE TABLE IF NOT EXISTS journal (destination TEXT NOT NULL, installation TEXT NOT NULL,
            update_ref TEXT NOT NULL, stream_ref TEXT NOT NULL, sequence INTEGER NOT NULL,
            digest TEXT NOT NULL, target TEXT NOT NULL, payload TEXT, outcome TEXT NOT NULL,
            provenance TEXT, receipt TEXT, created REAL NOT NULL, updated REAL NOT NULL,
            PRIMARY KEY(destination, update_ref), UNIQUE(destination, stream_ref, sequence));
          CREATE TABLE IF NOT EXISTS ownership (path TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        version = self.db.execute(
            "SELECT value FROM meta WHERE key='version'"
        ).fetchone()
        if version and version["value"] != "1":
            raise LocalError("state_upgrade_required")
        self.db.execute("INSERT OR IGNORE INTO meta VALUES ('version','1')")
        self.migrate_v2()

    def close(self):
        try:
            for remote in getattr(self, "remotes", {}).values():
                remote.close()
        finally:
            self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def migrate_v2(self):
        # Preserve the original file as a rollback backup; never write it again.
        # Invalid or label-only entries remain visible for explicit repair.
        if self.db.execute("SELECT 1 FROM meta WHERE key='v2_imported'").fetchone():
            return
        with self.transaction():
            if self.db.execute("SELECT 1 FROM meta WHERE key='v2_imported'").fetchone():
                return
            old = self.folder / "projects.json"
            if old.exists():
                try:
                    if old.is_symlink() or old.stat().st_size > 4 * 1024 * 1024:
                        raise ValueError("invalid legacy file")
                    value = json.loads(old.read_text(encoding="utf-8"))
                    if (
                        not isinstance(value, dict)
                        or value.get("version") != 2
                        or not isinstance(value.get("projects"), dict)
                    ):
                        raise ValueError("invalid legacy format")
                    projects = value["projects"]
                    for key, binding in projects.items():
                        if not isinstance(key, str) or not isinstance(binding, dict):
                            continue
                        binding = dict(
                            binding, transport="native_oauth", installation=None
                        )
                        if validate_target(binding.get("expected_target")) is None:
                            binding["repair_required"] = True
                        self.db.execute(
                            "INSERT OR IGNORE INTO bindings VALUES (?,?)",
                            (key, canonical(binding)),
                        )
                except (OSError, ValueError, KeyError, TypeError, AttributeError):
                    backup = old.with_name("projects.json.unreadable-" + uuid4().hex)
                    try:
                        os.replace(old, backup)
                    except OSError:
                        backup = old  # Keep diagnostics usable even when rename is forbidden.
                    self.db.execute(
                        "INSERT OR REPLACE INTO meta VALUES ('legacy_import',?)",
                        (canonical({"state": "unreadable", "backup": str(backup)}),),
                    )
            self.db.execute("INSERT INTO meta VALUES ('v2_imported','1')")

    def issues(self):
        row = self.db.execute(
            "SELECT value FROM meta WHERE key='legacy_import'"
        ).fetchone()
        issues = (
            [{"code": "legacy_bindings_unreadable", **json.loads(row["value"])}]
            if row
            else []
        )
        if (
            self.db.execute("SELECT COUNT(*) FROM contexts").fetchone()[0]
            >= MAX_METADATA
        ):
            issues.append(
                {
                    "code": "context_capacity_requires_repair",
                    "next": "Use reporting prune with an explicit inactivity window; retired chats require a fresh session.",
                }
            )
        return issues

    @staticmethod
    def _retired_bits(session):
        digest = hashlib.sha256(session.encode("utf-8")).digest()
        return [
            int.from_bytes(digest[i : i + 4], "big") % (RETIRED_FILTER_BYTES * 8)
            for i in (0, 4, 8, 12)
        ]

    def _prune_contexts(self, session, *, days=CONTEXT_DAYS):
        # Retired hashes prevent an old chat from silently changing company after
        # its full context/nonce is pruned. The fixed-size filter can only refuse
        # an extra session (fresh context required), never grant authority.
        row = self.db.execute(
            "SELECT value FROM meta WHERE key='retired_contexts'"
        ).fetchone()
        retired = (
            bytearray.fromhex(row["value"]) if row else bytearray(RETIRED_FILTER_BYTES)
        )
        old = list(
            self.db.execute(
                "SELECT session FROM turns WHERE updated<? AND session!=?",
                (time.time() - days * 86400, session),
            )
        )
        for item in old:
            identity = item["session"]
            for bit in self._retired_bits(identity):
                retired[bit // 8] |= 1 << (bit % 8)
            self.db.execute("DELETE FROM contexts WHERE session=?", (identity,))
            self.db.execute("DELETE FROM turns WHERE session=?", (identity,))
            self.db.execute(
                "DELETE FROM meta WHERE key=?",
                (
                    "fresh_context_notice:"
                    + hashlib.sha256(identity.encode()).hexdigest(),
                ),
            )
        if old:
            self.db.execute(
                "INSERT OR REPLACE INTO meta VALUES ('retired_contexts',?)",
                (retired.hex(),),
            )
        if session and (row or old):
            if all(
                retired[bit // 8] & (1 << (bit % 8))
                for bit in self._retired_bits(session)
            ):
                raise LocalError("retired_context_requires_fresh_session")
        return len(old)

    def retire_inactive(self, days=CONTEXT_DAYS):
        if type(days) is not int or not 0 <= days <= 3650:
            raise LocalError("invalid_retention_window")
        with self.transaction():
            return self._prune_contexts("", days=days)

    def bindings(self):
        return {
            row["key"]: json.loads(row["value"])
            for row in self.db.execute("SELECT * FROM bindings")
        }

    def bind(
        self,
        key,
        label,
        target,
        *,
        transport="native_oauth",
        installation=None,
        enabled=None,
    ):
        stable_target(target)
        if (
            not isinstance(label, str)
            or not label.strip()
            or len(label) > 200
            or not label.isprintable()
        ):
            raise LocalError("invalid_project_label")
        if (
            transport not in {"native_oauth", "api_key"}
            or transport == "api_key"
            and not installation
        ):
            raise LocalError("installation_required")
        binding = dict(
            project_label=label,
            expected_target=target,
            transport=transport,
            installation=installation,
            enabled=bool(enabled),
        )
        with self.transaction():
            prior = self.db.execute(
                "SELECT value FROM bindings WHERE key=?", (key,)
            ).fetchone()
            if enabled is None and prior:
                previous = json.loads(prior["value"])
                if (
                    validate_target(previous.get("expected_target"))
                    and stable_target(previous["expected_target"])
                    == stable_target(target)
                    and previous.get("transport", "native_oauth") == transport
                    and previous.get("installation") == installation
                ):
                    binding["enabled"] = previous.get("enabled", True)
            self.db.execute(
                "INSERT OR REPLACE INTO bindings VALUES (?,?)",
                (key, canonical(binding)),
            )
        return binding

    def unbind(self, key):
        with self.transaction():
            self.db.execute("DELETE FROM bindings WHERE key=?", (key,))

    def set_enabled(self, key, enabled):
        with self.transaction():
            row = self.db.execute(
                "SELECT value FROM bindings WHERE key=?", (key,)
            ).fetchone()
            if not row:
                raise LocalError("target_selection_required")
            binding = json.loads(row["value"])
            if enabled and validate_target(binding.get("expected_target")) is None:
                raise LocalError("binding_repair_required")
            binding["enabled"] = bool(enabled)
            self.db.execute(
                "UPDATE bindings SET value=? WHERE key=?", (canonical(binding), key)
            )

    def turn(self, session, target, *, new=False, event_id=None):
        destination = stable_target(target)
        with self.transaction():
            self._prune_contexts(session)
            prior = self.db.execute(
                "SELECT destination FROM contexts WHERE session=?", (session,)
            ).fetchone()
            if prior and prior["destination"] != destination:
                raise LocalError("fresh_context_required")
            if (
                prior is None
                and self.db.execute("SELECT COUNT(*) FROM contexts").fetchone()[0]
                >= MAX_METADATA
            ):
                raise LocalError("context_capacity_requires_repair")
            self.db.execute(
                "INSERT OR IGNORE INTO contexts VALUES (?,?)", (session, destination)
            )
            row = self.db.execute(
                "SELECT * FROM turns WHERE session=?", (session,)
            ).fetchone()
            # Explicit CLI callers can supply their own stable turn ID. Native
            # hooks cannot claim duplicate identity until a host field is qualified.
            if row is None or new and (event_id is None or row["event_id"] != event_id):
                nonce = str(uuid4())
                self.db.execute(
                    "INSERT OR REPLACE INTO turns VALUES (?,?,?,?,?,0,NULL,NULL,?)",
                    (session, destination, nonce, event_id, "open", time.time()),
                )
            return dict(
                self.db.execute(
                    "SELECT * FROM turns WHERE session=?", (session,)
                ).fetchone()
            )

    def remind_once(self, session, nonce):
        with self.transaction():
            result = self.db.execute(
                "UPDATE turns SET reminded=1 WHERE session=? AND nonce=? "
                "AND state IN ('open','unknown_send') AND reminded=0",
                (session, nonce),
            )
            return result.rowcount == 1

    def checkpoint(
        self, session, nonce, target, state, *, refs=(), provenance="host_reported"
    ):
        if state not in {
            "no_material_change",
            "captured_finalized",
            "blocked",
            "unknown_send",
            "repair_required",
            "discarded",
        }:
            raise LocalError("invalid_checkpoint")
        if provenance not in {"host_reported", "server_confirmed"}:
            raise LocalError("invalid_provenance")
        destination = stable_target(target)
        if state == "captured_finalized" and not refs:
            raise LocalError("capture_receipt_required")
        with self.transaction():
            if provenance == "server_confirmed":
                for ref in refs:
                    row = self.db.execute(
                        "SELECT outcome,provenance FROM journal WHERE destination=? AND update_ref=?",
                        (destination, ref),
                    ).fetchone()
                    if (
                        not row
                        or row["outcome"] != "captured"
                        or row["provenance"] != "server_confirmed"
                    ):
                        raise LocalError("capture_receipt_required")
            result = self.db.execute(
                "UPDATE turns SET state=?,provenance=?,refs=?,updated=? "
                "WHERE session=? AND nonce=? AND destination=?",
                (
                    state,
                    provenance,
                    canonical(list(refs)),
                    time.time(),
                    session,
                    nonce,
                    destination,
                ),
            )
            if result.rowcount != 1:
                raise LocalError("stale_turn_nonce")
        return {"state": state, "provenance": provenance, "nonce": nonce}

    def prepare(self, target, installation, payload):
        # Caller must pass canonical preflight output, never raw input.
        destination = stable_target(target)
        value = json.loads(payload)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        with self.transaction():
            prior = self.db.execute(
                "SELECT * FROM journal WHERE destination=? AND update_ref=?",
                (destination, value["update_ref"]),
            ).fetchone()
            if prior:
                if prior["digest"] != digest or prior["installation"] != installation:
                    raise LocalError("idempotency_conflict")
                return dict(prior)
            capacity = self.db.execute(
                "SELECT COUNT(*),COALESCE(SUM(LENGTH(CAST(payload AS BLOB))),0) "
                "FROM journal WHERE outcome NOT IN ('captured','discarded')"
            ).fetchone()
            if (
                capacity[0] >= MAX_PENDING
                or capacity[1] + len(payload.encode("utf-8")) > MAX_PENDING_BYTES
            ):
                raise LocalError("pending_capacity_exceeded")
            try:
                self.db.execute(
                    "INSERT INTO journal VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        destination,
                        installation,
                        value["update_ref"],
                        value["stream_ref"],
                        value["sequence"],
                        digest,
                        canonical(target),
                        payload,
                        "prepared",
                        None,
                        None,
                        time.time(),
                        time.time(),
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise LocalError("sequence_conflict") from exc
            return dict(
                self.db.execute(
                    "SELECT * FROM journal WHERE destination=? AND update_ref=?",
                    (destination, value["update_ref"]),
                ).fetchone()
            )

    def pending(self, target, ref, installation, *, allow_expired=False):
        row = self.db.execute(
            "SELECT * FROM journal WHERE destination=? AND update_ref=?",
            (stable_target(target), ref),
        ).fetchone()
        if not row or row["installation"] != installation:
            raise LocalError("original_destination_required")
        if row["outcome"] == "discarded":
            raise LocalError("pending_explicitly_discarded")
        if (
            not allow_expired
            and row["outcome"] != "captured"
            and row["created"] < time.time() - PENDING_DAYS * 86400
        ):
            raise LocalError("pending_expired_requires_disposition")
        if json.loads(row["target"]) != target:
            raise LocalError("authority_refresh_requires_repair")
        return dict(row)

    def outcome(self, row, outcome, receipt=None):
        if outcome not in {
            "unknown_send",
            "captured",
            "not_captured",
            "repair_required",
            "discarded",
        }:
            raise LocalError("invalid_delivery_state")
        with self.transaction():
            self.db.execute(
                "UPDATE journal SET outcome=?,receipt=?,payload=CASE WHEN ? IN ('captured','discarded') THEN NULL "
                "ELSE payload END, provenance=?,updated=? WHERE destination=? AND update_ref=? "
                "AND outcome NOT IN ('captured','discarded')",
                (
                    outcome,
                    canonical(receipt_metadata(receipt)) if receipt else None,
                    outcome,
                    "server_confirmed"
                    if outcome == "captured"
                    else "local_disposition"
                    if outcome == "discarded"
                    else None,
                    time.time(),
                    row["destination"],
                    row["update_ref"],
                ),
            )
            # Only captured metadata is eligible for bounded cleanup.
            self.db.execute(
                "DELETE FROM journal WHERE outcome IN ('captured','discarded') AND updated<?",
                (time.time() - METADATA_DAYS * 86400,),
            )
            self.db.execute(
                "DELETE FROM journal WHERE outcome IN ('captured','discarded') AND rowid NOT IN "
                "(SELECT rowid FROM journal ORDER BY updated DESC LIMIT ?)",
                (MAX_METADATA,),
            )
