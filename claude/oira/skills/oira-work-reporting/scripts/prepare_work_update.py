"""Local outbound preflight for Oira work updates (``oira_work_update.v2``).

Usage::

    python3 prepare_work_update.py < candidate.json
    python3 prepare_work_update.py --new-ref
    python3 prepare_work_update.py --history-stream SESSION_ID

The first form reads one candidate update on standard input, applies the
closed contract's allowlist and limits and a recursive credential scan, and
prints only the accepted canonical JSON. On refusal it prints field paths and
reason codes, never the rejected values. The second prints a fresh random
reference for ``update_ref`` or ``stream_ref``. The third prints the
``stream_ref`` of one past session in a history import: derived one way from
the coding app's own session id, so the same session always gets the same
reference while the id itself never leaves this computer.

Invoke this module with Python, as shown above; it is not a shell command.
Its only update input is standard input. It never reads environment variables,
credential files or authentication tokens. Credential names and remote URL
patterns below are rejection rules for the candidate, not data sources or
network destinations. Authentication belongs to the host's Oira MCP OAuth
connection and is not handled by this module.

The script uses the Python standard library only. It opens no network
connection, writes no files, keeps no logs and sends no telemetry. Exit codes:
0 accepted, 2 refused (rewrite the named fields and run it again), 3 reporting
unavailable on this host (nothing may be sent).

Its checks find recognized credential patterns; they cannot prove that an
arbitrary sentence contains no secret. Oira runs the same checks again before
it stores anything.

Canonical source: ``server/brain/v4/external_connectors/agent_sessions/mcp/
work_update_preflight.py`` in the Oira repository. The plugin copies
(``skills/oira-work-reporting/scripts/prepare_work_update.py``) are generated
from it and must not be edited.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import unicodedata
import uuid
from urllib.parse import parse_qsl, urlsplit


SCHEMA = 'oira_work_update.v2'
# The outbound filter this file implements. A skill reports it as
# ``privacy_policy_version``; the value is an assertion, not proof of a scan.
FILTER_POLICY_VERSION = 'oira_outbound_filter.v1'
MINIMUM_PYTHON = (3, 11)

MAX_RAW_INPUT_BYTES = 131_072
MAX_UPDATE_BYTES = 32_768
MAX_FINDINGS = 40

MAX_WORKS = 8
MAX_FACTS = 16
MAX_DETAILS = 12
MAX_MENTIONS = 16
MAX_REFERENCES = 12
MAX_RELATION_HINTS = 12
MAX_REVISIONS = 8
MAX_BOUNDARIES = 6
MAX_SUPPORTING_FACTS = 8
MAX_COMMITS = 20
MAX_PULL_REQUESTS = 10
MAX_SUBJECT_LABELS = 6
MAX_FUNCTION_LABELS = 4
MAX_VERSION_REFS = 6
MAX_SEQUENCE = 1_000_000_000

PROJECT_LABEL_MAX_CHARS = 200
TITLE_MAX_CHARS = 160
OUTCOME_MAX_BYTES = 1_200
BOUNDARY_MAX_BYTES = 600
STATEMENT_MAX_BYTES = 1_200
UNCERTAINTY_MAX_BYTES = 600
DEFERRAL_TEXT_MAX_BYTES = 600
DETAIL_DESCRIPTION_MAX_BYTES = 600
SAFE_LABEL_MAX_BYTES = 160
SUBJECT_LABEL_MAX_CHARS = 160
FUNCTION_LABEL_MAX_CHARS = 120
ENVIRONMENT_MAX_CHARS = 120
VERSION_REF_MAX_CHARS = 255
SAFE_URL_MAX_BYTES = 255
REPOSITORY_URL_MAX_CHARS = 300
BRANCH_MAX_CHARS = 200

ACTIVITIES = ('planning', 'execution', 'validation', 'mixed')
OPERATIONS = ('declare', 'update')
FACT_KINDS = (
    'decision', 'alternative', 'attempted_change', 'implemented_change',
    'commitment', 'assignment', 'explicit_deferral', 'verification',
    'blocker', 'question', 'next_step', 'limitation',
)
# The existing internal ClaimStatus vocabulary, unchanged.
CLAIM_STATUSES = (
    'proposed', 'accepted', 'attempted', 'tested', 'committed', 'merged',
    'released', 'unresolved', 'deferred', 'unknown',
)
STATUSES_BY_KIND = {
    'decision': ('proposed', 'accepted'),
    'alternative': ('proposed', 'unresolved'),
    'attempted_change': ('attempted',),
    'implemented_change': (
        'accepted', 'tested', 'committed', 'merged', 'released',
    ),
    'commitment': ('proposed', 'accepted'),
    'assignment': ('proposed', 'accepted'),
    'explicit_deferral': ('deferred',),
    'verification': ('tested', 'unresolved', 'unknown'),
    'blocker': ('unresolved',),
    'question': ('unresolved',),
    'next_step': ('proposed', 'accepted'),
    'limitation': ('unknown',),
}
DELIVERY_STATUSES = ('tested', 'committed', 'merged', 'released')
BASES = (
    'agent_report', 'user_statement_paraphrase', 'agent_inference',
    'relayed_report',
)
# Absent: the user's current work. ``history_import``: work from a past
# session the member asked Oira to import; every fact then says when it
# happened, inside the window Oira gave.
ORIGINS = ('history_import',)
DETAIL_KINDS = (
    'surface', 'input_output', 'assumption', 'behavior', 'transform',
    'verification', 'decision', 'open_point', 'contribution',
)
TEMPORAL_STATUSES = ('proposed', 'current', 'superseded', 'unknown')
VERSION_REF_KINDS = (
    'git_commit', 'pull_request', 'branch', 'model', 'prompt',
    'retrieval_index', 'dataset', 'schema', 'mobile_build', 'api', 'sdk',
    'mcp_server', 'artifact_version',
)
ENTITY_KINDS = (
    'person', 'team_agent', 'function', 'project', 'repository', 'file',
    'symbol', 'task', 'discussion', 'artifact',
)
REFERENCE_KINDS = (
    'work_item', 'artifact', 'discussion', 'external_task', 'pull_request',
    'issue', 'repository', 'source_object',
)
TARGET_KINDS = ('returned_handle', 'work_ref', 'safe_url')
TARGET_KINDS_BY_REFERENCE = {
    'work_item': ('returned_handle', 'work_ref'),
    'artifact': ('returned_handle',),
    'discussion': ('returned_handle',),
    'source_object': ('returned_handle',),
    'external_task': ('safe_url',),
    'pull_request': ('safe_url',),
    'issue': ('safe_url',),
    'repository': ('safe_url',),
}
RELATION_KINDS = (
    'same_work', 'new_work', 'related', 'depends_on', 'blocks',
    'conflicts_with', 'duplicate', 'possibly_same_as',
)
SYMMETRIC_RELATION_KINDS = (
    'same_work', 'conflicts_with', 'duplicate', 'possibly_same_as',
)
RELATION_DIRECTIONS = (
    'primary_to_target', 'target_to_primary', 'symmetric', 'not_applicable',
)
CONTINUITY_RELATIONSHIPS = (
    'continues_prior', 'returns_to_prior', 'new_work', 'corrects_prior',
    'reviews_completed', 'resumes_completed', 'follow_up',
)
CONTINUITY_TARGET_KINDS = ('returned_handle', 'work_ref')
# Relationships about one earlier piece of work. An update may name its own
# work with one of them (for example resuming its own completed work).
PRIOR_WORK_RELATIONSHIPS = (
    'continues_prior', 'returns_to_prior', 'corrects_prior',
    'reviews_completed', 'resumes_completed',
)
REVISION_KINDS = ('corrects', 'supersedes', 'reaffirms')

LOCAL_REF = re.compile(r'^[a-z][a-z0-9_-]{0,63}$')
RANDOM_REF = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
)
VERSION_TEXT = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._+-]{0,39}$')
CONFIDENCE = re.compile(r'^(?:0(?:\.[0-9]{1,4})?|1(?:\.0{1,4})?)$')
RFC3339 = re.compile(
    r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}'
    r'(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})$'
)
# Server-issued opaque handles: a work handle, or a fact handle naming the
# update unit it was reported in and its own local fact label.
WORK_HANDLE = re.compile(r'^wh_[a-z2-7]{26}$')
FACT_HANDLE = re.compile(r'^uh_[a-z2-7]{26}\.[a-z][a-z0-9_-]{0,63}$')
RETURNED_HANDLE = WORK_HANDLE
GIT_SHA = re.compile(r'^[0-9a-f]{7,40}$')
GIT_BRANCH = re.compile(r'^(?!-)(?!.*\.\.)[^\x00-\x20\x7f~^:?*\[\\]{1,200}$')
SCP_REMOTE = re.compile(
    r'^(?:[A-Za-z0-9._-]+@)?(?P<host>[A-Za-z0-9.-]+):(?P<path>[A-Za-z0-9._~/-]+)$'
)

ENVELOPE_FIELDS = {
    'schema', 'project_label', 'update_ref', 'stream_ref', 'sequence',
    'works', 'reporter_version', 'privacy_policy_version', 'origin',
    'session_complete',
}
WORK_FIELDS = {
    'work_ref', 'operation', 'title', 'intended_outcome', 'activity',
    'boundaries', 'facts', 'details', 'mentions', 'references',
    'relation_hints', 'code', 'continuity', 'deferral', 'revisions',
}
FACT_FIELDS = {
    'fact_ref', 'kind', 'status', 'statement', 'basis', 'confidence',
    'occurred_at', 'uncertainty', 'repeats',
}
DETAIL_FIELDS = {
    'detail_ref', 'kind', 'description', 'subject_labels', 'function_labels',
    'environment', 'version_refs', 'temporal_status', 'uncertainty',
    'supporting_fact_refs',
}
VERSION_REF_FIELDS = {'ref_kind', 'ref'}
MENTION_FIELDS = {
    'mention_ref', 'entity_kind', 'safe_label', 'supporting_fact_refs',
}
REFERENCE_FIELDS = {
    'reference_ref', 'reference_kind', 'target', 'supporting_fact_refs',
}
TARGET_FIELDS = {'kind', 'value'}
RELATION_FIELDS = {
    'relation_kind', 'target_reference_ref', 'direction',
    'supporting_fact_refs',
}
CODE_FIELDS = {'repository_url', 'branch', 'commits', 'pull_requests'}
CONTINUITY_FIELDS = {'relationship', 'target', 'supporting_fact_refs'}
DEFERRAL_FIELDS = {
    'reason', 'resume_condition', 'resume_after', 'origin_work_ref',
    'supporting_fact_refs',
}
REVISION_FIELDS = {'fact_handle', 'revision_kind', 'supporting_fact_refs'}
# A finding's path is built from these names and list indices only. A key
# the candidate made up is never repeated (it could itself hold a secret):
# it is shown as ``*``.
PATH_NAMES = frozenset().union(
    ENVELOPE_FIELDS, WORK_FIELDS, FACT_FIELDS, DETAIL_FIELDS,
    VERSION_REF_FIELDS, MENTION_FIELDS, REFERENCE_FIELDS, TARGET_FIELDS,
    RELATION_FIELDS, CODE_FIELDS, CONTINUITY_FIELDS, DEFERRAL_FIELDS,
    REVISION_FIELDS,
)
UNKNOWN_KEY = '*'
MAX_PATH_CHARS = 160

# Reason codes. Structural codes name the rule a field broke; ``secret.*``
# and ``privacy.*`` codes name the kind of value found, never the value.
REASON_CODES = (
    'input_too_large', 'input_not_utf8', 'input_not_json', 'duplicate_key',
    'non_finite_number', 'invalid_unicode', 'update_too_large',
    'required', 'unknown_field', 'wrong_type', 'not_allowed', 'too_long',
    'too_short', 'too_many', 'too_few', 'invalid_format', 'not_trimmed',
    'control_character', 'hidden_character', 'duplicate', 'not_canonical',
    'out_of_range', 'unknown_fact_ref', 'unknown_reference_ref',
    'self_reference', 'declare_requires_field',
    'declare_requires_commitment_or_deferral',
    'status_not_allowed_for_kind', 'inference_cannot_assert_delivery',
    'deferral_required', 'deferral_requires_deferred_fact',
    'relation_direction_invalid', 'relation_target_required',
    'relation_target_forbidden', 'continuity_target_required',
    'continuity_target_forbidden', 'reference_target_not_allowed',
    'required_for_history_import', 'history_import_only',
    'secret.private_key', 'secret.provider_key', 'secret.authorization',
    'secret.sensitive_assignment', 'secret.jwt', 'secret.credential_url',
    'secret.sensitive_url_parameter', 'secret.webhook_url',
    'secret.opaque_blob', 'privacy.local_path',
    'preflight_internal_error', 'python_version_unsupported',
)


class Finding(tuple):
    """One refusal: where (a JSON path) and why (a reason code)."""

    __slots__ = ()

    def __new__(cls, path: str, code: str):
        return tuple.__new__(cls, (str(path)[:MAX_PATH_CHARS], code))

    @property
    def path(self) -> str:
        return self[0]

    @property
    def code(self) -> str:
        return self[1]

    def wire(self) -> dict:
        return {'path': self[0], 'code': self[1]}


class CandidateRefused(ValueError):
    def __init__(self, findings):
        super().__init__('candidate refused')
        self.findings = list(findings)


# ── Strict JSON input ─────────────────────────────────────────────────────


def _reject_duplicates(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise CandidateRefused([Finding('$', 'duplicate_key')])
        seen[key] = value
    return seen


def _reject_constant(_name):
    raise CandidateRefused([Finding('$', 'non_finite_number')])


def _parse_float(text):
    value = float(text)
    if not math.isfinite(value):
        raise CandidateRefused([Finding('$', 'non_finite_number')])
    return value


def load_candidate(raw) -> object:
    """Parse one candidate with a size cap, strict UTF-8 and unique keys."""

    if isinstance(raw, str):
        try:
            raw = raw.encode('utf-8')
        except UnicodeEncodeError:
            raise CandidateRefused([Finding('$', 'invalid_unicode')])
    if len(raw) > MAX_RAW_INPUT_BYTES:
        raise CandidateRefused([Finding('$', 'input_too_large')])
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        raise CandidateRefused([Finding('$', 'input_not_utf8')])
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicates,
            parse_constant=_reject_constant,
            parse_float=_parse_float,
        )
    except CandidateRefused:
        raise
    except (ValueError, RecursionError):
        raise CandidateRefused([Finding('$', 'input_not_json')])


# ── Canonical form ────────────────────────────────────────────────────────


def _without_nulls(value):
    if isinstance(value, dict):
        return {
            key: _without_nulls(item) for key, item in value.items()
            if item is not None
        }
    if isinstance(value, list):
        return [_without_nulls(item) for item in value]
    return value


def canonical_json(value) -> str:
    """Sorted keys, no insignificant whitespace, no null members."""

    return json.dumps(
        _without_nulls(value), sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False,
    )


def canonical_bytes(value) -> bytes:
    return canonical_json(value).encode('utf-8')


# ── Structural validation ─────────────────────────────────────────────────


def _hidden(char: str) -> bool:
    return unicodedata.category(char) in ('Cf', 'Co')


def _text_findings(path, value, *, max_chars=None, max_bytes=None):
    if not isinstance(value, str):
        return [Finding(path, 'wrong_type')]
    if any(unicodedata.category(char) == 'Cs' for char in value):
        return [Finding(path, 'invalid_unicode')]
    if not value.strip():
        return [Finding(path, 'too_short')]
    found = []
    if value != value.strip():
        found.append(Finding(path, 'not_trimmed'))
    if any(unicodedata.category(char) == 'Cc' for char in value):
        found.append(Finding(path, 'control_character'))
    if any(_hidden(char) for char in value):
        found.append(Finding(path, 'hidden_character'))
    if max_chars is not None and len(value) > max_chars:
        found.append(Finding(path, 'too_long'))
    if max_bytes is not None and len(value.encode('utf-8')) > max_bytes:
        found.append(Finding(path, 'too_long'))
    return found


def _token_findings(path, value, pattern):
    if not isinstance(value, str):
        return [Finding(path, 'wrong_type')]
    if pattern.fullmatch(value) is None:
        return [Finding(path, 'invalid_format')]
    return []


def _enum_findings(path, value, allowed):
    if not isinstance(value, str):
        return [Finding(path, 'wrong_type')]
    if value not in allowed:
        return [Finding(path, 'not_allowed')]
    return []


def _timestamp_findings(path, value):
    if not isinstance(value, str):
        return [Finding(path, 'wrong_type')]
    if RFC3339.fullmatch(value) is None:
        return [Finding(path, 'invalid_format')]
    from datetime import datetime

    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return [Finding(path, 'invalid_format')]
    if parsed.tzinfo is None:
        return [Finding(path, 'invalid_format')]
    return []


def _object(path, value, allowed, required=()):
    """(object or None, findings) for a closed object."""

    if not isinstance(value, dict):
        return None, [Finding(path, 'wrong_type')]
    found = (
        [Finding(_join(path, UNKNOWN_KEY), 'unknown_field')]
        if set(value) - set(allowed) else []
    )
    for key in required:
        if value.get(key) is None:
            found.append(Finding(_join(path, key), 'required'))
    return value, found


def _join(path, key):
    return key if path == '$' else f'{path}.{key}'


def _list(path, value, *, maximum, minimum=0):
    if not isinstance(value, list):
        return None, [Finding(path, 'wrong_type')]
    found = []
    if len(value) > maximum:
        found.append(Finding(path, 'too_many'))
    if len(value) < minimum:
        found.append(Finding(path, 'too_few'))
    return value, found


def _present(value, key):
    return isinstance(value, dict) and value.get(key) is not None


def _supporting_findings(path, value, fact_refs):
    items, found = _list(path, value, maximum=MAX_SUPPORTING_FACTS, minimum=1)
    if items is None:
        return found
    seen = set()
    for index, item in enumerate(items):
        item_path = f'{path}[{index}]'
        problems = _token_findings(item_path, item, LOCAL_REF)
        if problems:
            found.extend(problems)
            continue
        if item in seen:
            found.append(Finding(item_path, 'duplicate'))
        seen.add(item)
        if item not in fact_refs:
            found.append(Finding(item_path, 'unknown_fact_ref'))
    return found


def safe_repository_url(value) -> str | None:
    """A git remote with credentials, query and fragment removed.

    Remotes can carry tokens (``https://user:token@host/...``); nothing but
    the host and path is kept. Returns None for anything unusable. The same
    sanitizer the v1 report contract uses; v2 requires the canonical result.
    """

    text = str(value or '').strip()
    if not text or any(char.isspace() for char in text):
        return None
    if '://' not in text:
        match = SCP_REMOTE.fullmatch(text)
        if match is None:
            return None
        return f'{match.group("host").lower()}:{match.group("path")}'
    try:
        parts = urlsplit(text)
        port = parts.port
    except ValueError:
        return None
    if parts.scheme not in ('https', 'http', 'ssh', 'git') or not parts.hostname:
        return None
    if not parts.path or parts.path == '/':
        return None
    host = parts.hostname.lower() + (f':{port}' if port else '')
    return f'{parts.scheme}://{host}{parts.path}'


def _safe_url_findings(path, value):
    found = _text_findings(path, value, max_bytes=SAFE_URL_MAX_BYTES)
    if found:
        return found
    if any(char.isspace() for char in value):
        return [Finding(path, 'invalid_format')]
    try:
        parts = urlsplit(value)
        parts.port
    except ValueError:
        return [Finding(path, 'invalid_format')]
    if parts.scheme != 'https' or not parts.hostname:
        return [Finding(path, 'invalid_format')]
    # Credentials in a URL are a secret finding, reported by the scan.
    return []


def _code_findings(path, value):
    code, found = _object(path, value, CODE_FIELDS)
    if code is None:
        return found
    if not any(code.get(key) for key in CODE_FIELDS):
        found.append(Finding(path, 'too_few'))
    if code.get('repository_url') is not None:
        item_path = _join(path, 'repository_url')
        problems = _text_findings(
            item_path, code['repository_url'],
            max_chars=REPOSITORY_URL_MAX_CHARS,
        )
        if problems:
            found.extend(problems)
        elif safe_repository_url(code['repository_url']) is None:
            found.append(Finding(item_path, 'invalid_format'))
        elif safe_repository_url(code['repository_url']) != code['repository_url']:
            found.append(Finding(item_path, 'not_canonical'))
    if code.get('branch') is not None:
        item_path = _join(path, 'branch')
        problems = _text_findings(item_path, code['branch'], max_chars=BRANCH_MAX_CHARS)
        if problems:
            found.extend(problems)
        elif GIT_BRANCH.fullmatch(code['branch']) is None:
            found.append(Finding(item_path, 'invalid_format'))
    if code.get('commits') is not None:
        items, problems = _list(
            _join(path, 'commits'), code['commits'], maximum=MAX_COMMITS,
        )
        found.extend(problems)
        seen = set()
        for index, item in enumerate(items or ()):
            item_path = f'{_join(path, "commits")}[{index}]'
            problems = _token_findings(item_path, item, GIT_SHA)
            found.extend(problems)
            if not problems:
                if item in seen:
                    found.append(Finding(item_path, 'duplicate'))
                seen.add(item)
    if code.get('pull_requests') is not None:
        items, problems = _list(
            _join(path, 'pull_requests'), code['pull_requests'],
            maximum=MAX_PULL_REQUESTS,
        )
        found.extend(problems)
        seen = set()
        for index, item in enumerate(items or ()):
            item_path = f'{_join(path, "pull_requests")}[{index}]'
            if isinstance(item, bool) or not isinstance(item, int):
                found.append(Finding(item_path, 'wrong_type'))
                continue
            if not 0 < item < 100_000_000:
                found.append(Finding(item_path, 'out_of_range'))
                continue
            if item in seen:
                found.append(Finding(item_path, 'duplicate'))
            seen.add(item)
    return found


def _target_findings(path, value, allowed_kinds, *, own_work_ref, allow_self=False):
    target, found = _object(path, value, TARGET_FIELDS, ('kind', 'value'))
    if target is None or found:
        return found
    kind = target['kind']
    found.extend(_enum_findings(_join(path, 'kind'), kind, TARGET_KINDS))
    if found:
        return found
    if kind not in allowed_kinds:
        return [Finding(_join(path, 'kind'), 'reference_target_not_allowed')]
    value_path = _join(path, 'value')
    if kind == 'returned_handle':
        return _token_findings(value_path, target['value'], RETURNED_HANDLE)
    if kind == 'work_ref':
        problems = _token_findings(value_path, target['value'], LOCAL_REF)
        if not problems and target['value'] == own_work_ref and not allow_self:
            problems.append(Finding(value_path, 'self_reference'))
        return problems
    return _safe_url_findings(value_path, target['value'])


def _fact_findings(path, value):
    fact, found = _object(
        path, value, FACT_FIELDS,
        ('fact_ref', 'kind', 'status', 'statement', 'basis', 'confidence'),
    )
    if fact is None:
        return found
    if fact.get('fact_ref') is not None:
        found.extend(_token_findings(_join(path, 'fact_ref'), fact['fact_ref'], LOCAL_REF))
    kind_ok = status_ok = False
    if fact.get('kind') is not None:
        problems = _enum_findings(_join(path, 'kind'), fact['kind'], FACT_KINDS)
        found.extend(problems)
        kind_ok = not problems
    if fact.get('status') is not None:
        problems = _enum_findings(_join(path, 'status'), fact['status'], CLAIM_STATUSES)
        found.extend(problems)
        status_ok = not problems
    if kind_ok and status_ok and fact['status'] not in STATUSES_BY_KIND[fact['kind']]:
        found.append(Finding(_join(path, 'status'), 'status_not_allowed_for_kind'))
    if fact.get('statement') is not None:
        found.extend(_text_findings(
            _join(path, 'statement'), fact['statement'],
            max_bytes=STATEMENT_MAX_BYTES,
        ))
    if fact.get('basis') is not None:
        problems = _enum_findings(_join(path, 'basis'), fact['basis'], BASES)
        found.extend(problems)
        if (
            not problems and status_ok and fact['basis'] == 'agent_inference'
            and fact['status'] in DELIVERY_STATUSES
        ):
            found.append(Finding(_join(path, 'status'), 'inference_cannot_assert_delivery'))
    if fact.get('confidence') is not None:
        found.extend(_token_findings(
            _join(path, 'confidence'), fact['confidence'], CONFIDENCE,
        ))
    if fact.get('occurred_at') is not None:
        found.extend(_timestamp_findings(_join(path, 'occurred_at'), fact['occurred_at']))
    if fact.get('uncertainty') is not None:
        found.extend(_text_findings(
            _join(path, 'uncertainty'), fact['uncertainty'],
            max_bytes=UNCERTAINTY_MAX_BYTES,
        ))
    if fact.get('repeats') is not None:
        found.extend(_token_findings(
            _join(path, 'repeats'), fact['repeats'], FACT_HANDLE,
        ))
    return found


def _labels_findings(path, value, *, maximum, max_chars):
    items, found = _list(path, value, maximum=maximum)
    seen = set()
    for index, item in enumerate(items or ()):
        item_path = f'{path}[{index}]'
        problems = _text_findings(item_path, item, max_chars=max_chars)
        found.extend(problems)
        if not problems:
            if item in seen:
                found.append(Finding(item_path, 'duplicate'))
            seen.add(item)
    return found


def _detail_findings(path, value, fact_refs):
    detail, found = _object(
        path, value, DETAIL_FIELDS,
        ('detail_ref', 'kind', 'description', 'temporal_status',
         'supporting_fact_refs'),
    )
    if detail is None:
        return found
    if detail.get('detail_ref') is not None:
        found.extend(_token_findings(_join(path, 'detail_ref'), detail['detail_ref'], LOCAL_REF))
    if detail.get('kind') is not None:
        found.extend(_enum_findings(_join(path, 'kind'), detail['kind'], DETAIL_KINDS))
    if detail.get('description') is not None:
        found.extend(_text_findings(
            _join(path, 'description'), detail['description'],
            max_bytes=DETAIL_DESCRIPTION_MAX_BYTES,
        ))
    if detail.get('subject_labels') is not None:
        found.extend(_labels_findings(
            _join(path, 'subject_labels'), detail['subject_labels'],
            maximum=MAX_SUBJECT_LABELS, max_chars=SUBJECT_LABEL_MAX_CHARS,
        ))
    if detail.get('function_labels') is not None:
        found.extend(_labels_findings(
            _join(path, 'function_labels'), detail['function_labels'],
            maximum=MAX_FUNCTION_LABELS, max_chars=FUNCTION_LABEL_MAX_CHARS,
        ))
    if detail.get('environment') is not None:
        found.extend(_text_findings(
            _join(path, 'environment'), detail['environment'],
            max_chars=ENVIRONMENT_MAX_CHARS,
        ))
    if detail.get('version_refs') is not None:
        refs_path = _join(path, 'version_refs')
        items, problems = _list(refs_path, detail['version_refs'], maximum=MAX_VERSION_REFS)
        found.extend(problems)
        seen = set()
        for index, item in enumerate(items or ()):
            item_path = f'{refs_path}[{index}]'
            ref, problems = _object(item_path, item, VERSION_REF_FIELDS, ('ref_kind', 'ref'))
            found.extend(problems)
            if ref is None or problems:
                continue
            problems = _enum_findings(_join(item_path, 'ref_kind'), ref['ref_kind'], VERSION_REF_KINDS)
            problems += _text_findings(
                _join(item_path, 'ref'), ref['ref'], max_chars=VERSION_REF_MAX_CHARS,
            )
            if not problems and any(char.isspace() for char in ref['ref']):
                problems.append(Finding(_join(item_path, 'ref'), 'invalid_format'))
            found.extend(problems)
            if not problems:
                key = (ref['ref_kind'], ref['ref'])
                if key in seen:
                    found.append(Finding(item_path, 'duplicate'))
                seen.add(key)
    if detail.get('temporal_status') is not None:
        found.extend(_enum_findings(
            _join(path, 'temporal_status'), detail['temporal_status'],
            TEMPORAL_STATUSES,
        ))
    if detail.get('uncertainty') is not None:
        found.extend(_text_findings(
            _join(path, 'uncertainty'), detail['uncertainty'],
            max_bytes=UNCERTAINTY_MAX_BYTES,
        ))
    if detail.get('supporting_fact_refs') is not None:
        found.extend(_supporting_findings(
            _join(path, 'supporting_fact_refs'), detail['supporting_fact_refs'],
            fact_refs,
        ))
    return found


def _work_findings(path, value, fact_refs_by_work=None):
    work, found = _object(
        path, value, WORK_FIELDS, ('work_ref', 'operation', 'facts'),
    )
    if work is None:
        return found
    own = work.get('work_ref') if isinstance(work.get('work_ref'), str) else None
    if work.get('work_ref') is not None:
        found.extend(_token_findings(_join(path, 'work_ref'), work['work_ref'], LOCAL_REF))
    operation = work.get('operation')
    if operation is not None:
        found.extend(_enum_findings(_join(path, 'operation'), operation, OPERATIONS))
    if operation == 'declare':
        for key in ('title', 'intended_outcome', 'activity'):
            if work.get(key) is None:
                found.append(Finding(_join(path, key), 'declare_requires_field'))
    if work.get('title') is not None:
        found.extend(_text_findings(_join(path, 'title'), work['title'], max_chars=TITLE_MAX_CHARS))
    if work.get('intended_outcome') is not None:
        found.extend(_text_findings(
            _join(path, 'intended_outcome'), work['intended_outcome'],
            max_bytes=OUTCOME_MAX_BYTES,
        ))
    if work.get('activity') is not None:
        found.extend(_enum_findings(_join(path, 'activity'), work['activity'], ACTIVITIES))
    if work.get('boundaries') is not None:
        boundaries_path = _join(path, 'boundaries')
        items, problems = _list(boundaries_path, work['boundaries'], maximum=MAX_BOUNDARIES)
        found.extend(problems)
        seen = set()
        for index, item in enumerate(items or ()):
            item_path = f'{boundaries_path}[{index}]'
            problems = _text_findings(item_path, item, max_bytes=BOUNDARY_MAX_BYTES)
            found.extend(problems)
            if not problems:
                if item in seen:
                    found.append(Finding(item_path, 'duplicate'))
                seen.add(item)

    fact_refs = set()
    fact_kinds = {}
    if work.get('facts') is not None:
        facts_path = _join(path, 'facts')
        items, problems = _list(facts_path, work['facts'], maximum=MAX_FACTS, minimum=1)
        found.extend(problems)
        for index, item in enumerate(items or ()):
            item_path = f'{facts_path}[{index}]'
            found.extend(_fact_findings(item_path, item))
            ref = item.get('fact_ref') if isinstance(item, dict) else None
            if isinstance(ref, str) and LOCAL_REF.fullmatch(ref):
                if ref in fact_refs:
                    found.append(Finding(_join(item_path, 'fact_ref'), 'duplicate'))
                fact_refs.add(ref)
                if isinstance(item.get('kind'), str):
                    fact_kinds[ref] = item['kind']
        kinds = {
            item['kind'] for item in (items or ())
            if isinstance(item, dict) and isinstance(item.get('kind'), str)
        }
        if operation == 'declare' and items and not kinds & {
            'commitment', 'explicit_deferral',
        }:
            found.append(Finding(facts_path, 'declare_requires_commitment_or_deferral'))
        if 'explicit_deferral' in kinds and work.get('deferral') is None:
            found.append(Finding(_join(path, 'deferral'), 'deferral_required'))

    for key, fields, limit, ref_key in (
        ('details', DETAIL_FIELDS, MAX_DETAILS, 'detail_ref'),
        ('mentions', MENTION_FIELDS, MAX_MENTIONS, 'mention_ref'),
        ('references', REFERENCE_FIELDS, MAX_REFERENCES, 'reference_ref'),
    ):
        if work.get(key) is None:
            continue
        list_path = _join(path, key)
        items, problems = _list(list_path, work[key], maximum=limit)
        found.extend(problems)
        labels = set()
        for index, item in enumerate(items or ()):
            item_path = f'{list_path}[{index}]'
            if key == 'details':
                found.extend(_detail_findings(item_path, item, fact_refs))
            elif key == 'mentions':
                found.extend(_mention_findings(item_path, item, fact_refs))
            else:
                found.extend(_reference_findings(item_path, item, fact_refs, own))
            label = item.get(ref_key) if isinstance(item, dict) else None
            if isinstance(label, str) and LOCAL_REF.fullmatch(label):
                if label in labels:
                    found.append(Finding(_join(item_path, ref_key), 'duplicate'))
                labels.add(label)

    reference_refs = {
        item.get('reference_ref') for item in (work.get('references') or ())
        if isinstance(item, dict) and isinstance(item.get('reference_ref'), str)
    } if isinstance(work.get('references'), list) else set()
    if work.get('relation_hints') is not None:
        hints_path = _join(path, 'relation_hints')
        items, problems = _list(hints_path, work['relation_hints'], maximum=MAX_RELATION_HINTS)
        found.extend(problems)
        for index, item in enumerate(items or ()):
            found.extend(_relation_findings(
                f'{hints_path}[{index}]', item, fact_refs, reference_refs,
            ))
    if work.get('code') is not None:
        found.extend(_code_findings(_join(path, 'code'), work['code']))
    if work.get('continuity') is not None:
        found.extend(_continuity_findings(
            _join(path, 'continuity'), work['continuity'], fact_refs, own,
            operation=operation,
        ))
    if work.get('deferral') is not None:
        found.extend(_deferral_findings(
            _join(path, 'deferral'), work['deferral'], fact_refs, fact_kinds, own,
        ))
    if work.get('revisions') is not None:
        revisions_path = _join(path, 'revisions')
        items, problems = _list(revisions_path, work['revisions'], maximum=MAX_REVISIONS)
        found.extend(problems)
        seen = set()
        for index, item in enumerate(items or ()):
            item_path = f'{revisions_path}[{index}]'
            revision, problems = _object(
                item_path, item, REVISION_FIELDS,
                ('fact_handle', 'revision_kind', 'supporting_fact_refs'),
            )
            found.extend(problems)
            if revision is None:
                continue
            if revision.get('fact_handle') is not None:
                problems = _token_findings(
                    _join(item_path, 'fact_handle'), revision['fact_handle'],
                    FACT_HANDLE,
                )
                found.extend(problems)
                if not problems:
                    if revision['fact_handle'] in seen:
                        found.append(Finding(_join(item_path, 'fact_handle'), 'duplicate'))
                    seen.add(revision['fact_handle'])
            if revision.get('revision_kind') is not None:
                found.extend(_enum_findings(
                    _join(item_path, 'revision_kind'), revision['revision_kind'],
                    REVISION_KINDS,
                ))
            if revision.get('supporting_fact_refs') is not None:
                found.extend(_supporting_findings(
                    _join(item_path, 'supporting_fact_refs'),
                    revision['supporting_fact_refs'], fact_refs,
                ))
    return found


def _mention_findings(path, value, fact_refs):
    mention, found = _object(
        path, value, MENTION_FIELDS,
        ('mention_ref', 'entity_kind', 'safe_label', 'supporting_fact_refs'),
    )
    if mention is None:
        return found
    if mention.get('mention_ref') is not None:
        found.extend(_token_findings(_join(path, 'mention_ref'), mention['mention_ref'], LOCAL_REF))
    if mention.get('entity_kind') is not None:
        found.extend(_enum_findings(_join(path, 'entity_kind'), mention['entity_kind'], ENTITY_KINDS))
    if mention.get('safe_label') is not None:
        found.extend(_text_findings(
            _join(path, 'safe_label'), mention['safe_label'],
            max_bytes=SAFE_LABEL_MAX_BYTES,
        ))
    if mention.get('supporting_fact_refs') is not None:
        found.extend(_supporting_findings(
            _join(path, 'supporting_fact_refs'), mention['supporting_fact_refs'],
            fact_refs,
        ))
    return found


def _reference_findings(path, value, fact_refs, own_work_ref):
    reference, found = _object(
        path, value, REFERENCE_FIELDS,
        ('reference_ref', 'reference_kind', 'target', 'supporting_fact_refs'),
    )
    if reference is None:
        return found
    if reference.get('reference_ref') is not None:
        found.extend(_token_findings(
            _join(path, 'reference_ref'), reference['reference_ref'], LOCAL_REF,
        ))
    kind = reference.get('reference_kind')
    kind_ok = False
    if kind is not None:
        problems = _enum_findings(_join(path, 'reference_kind'), kind, REFERENCE_KINDS)
        found.extend(problems)
        kind_ok = not problems
    if reference.get('target') is not None:
        found.extend(_target_findings(
            _join(path, 'target'), reference['target'],
            TARGET_KINDS_BY_REFERENCE[kind] if kind_ok else TARGET_KINDS,
            own_work_ref=own_work_ref,
        ))
    if reference.get('supporting_fact_refs') is not None:
        found.extend(_supporting_findings(
            _join(path, 'supporting_fact_refs'), reference['supporting_fact_refs'],
            fact_refs,
        ))
    return found


def _relation_findings(path, value, fact_refs, reference_refs):
    relation, found = _object(
        path, value, RELATION_FIELDS,
        ('relation_kind', 'direction', 'supporting_fact_refs'),
    )
    if relation is None:
        return found
    kind = relation.get('relation_kind')
    direction = relation.get('direction')
    kind_ok = direction_ok = False
    if kind is not None:
        problems = _enum_findings(_join(path, 'relation_kind'), kind, RELATION_KINDS)
        found.extend(problems)
        kind_ok = not problems
    if direction is not None:
        problems = _enum_findings(_join(path, 'direction'), direction, RELATION_DIRECTIONS)
        found.extend(problems)
        direction_ok = not problems
    target = relation.get('target_reference_ref')
    if target is not None:
        problems = _token_findings(_join(path, 'target_reference_ref'), target, LOCAL_REF)
        found.extend(problems)
        if not problems and target not in reference_refs:
            found.append(Finding(_join(path, 'target_reference_ref'), 'unknown_reference_ref'))
    if kind_ok and direction_ok:
        if kind in SYMMETRIC_RELATION_KINDS and direction != 'symmetric':
            found.append(Finding(_join(path, 'direction'), 'relation_direction_invalid'))
        if kind == 'new_work':
            if target is not None:
                found.append(Finding(_join(path, 'target_reference_ref'), 'relation_target_forbidden'))
            if direction != 'not_applicable':
                found.append(Finding(_join(path, 'direction'), 'relation_direction_invalid'))
        elif target is None:
            found.append(Finding(_join(path, 'target_reference_ref'), 'relation_target_required'))
    if relation.get('supporting_fact_refs') is not None:
        found.extend(_supporting_findings(
            _join(path, 'supporting_fact_refs'), relation['supporting_fact_refs'],
            fact_refs,
        ))
    return found


def _continuity_findings(path, value, fact_refs, own_work_ref, *, operation=None):
    continuity, found = _object(
        path, value, CONTINUITY_FIELDS, ('relationship', 'supporting_fact_refs'),
    )
    if continuity is None:
        return found
    relationship = continuity.get('relationship')
    if relationship is not None:
        problems = _enum_findings(
            _join(path, 'relationship'), relationship, CONTINUITY_RELATIONSHIPS,
        )
        found.extend(problems)
        if not problems:
            if relationship == 'new_work' and continuity.get('target') is not None:
                found.append(Finding(_join(path, 'target'), 'continuity_target_forbidden'))
            if relationship != 'new_work' and continuity.get('target') is None:
                found.append(Finding(_join(path, 'target'), 'continuity_target_required'))
    if continuity.get('target') is not None:
        found.extend(_target_findings(
            _join(path, 'target'), continuity['target'], CONTINUITY_TARGET_KINDS,
            own_work_ref=own_work_ref,
            allow_self=(
                operation == 'update'
                and relationship in PRIOR_WORK_RELATIONSHIPS
            ),
        ))
    if continuity.get('supporting_fact_refs') is not None:
        found.extend(_supporting_findings(
            _join(path, 'supporting_fact_refs'), continuity['supporting_fact_refs'],
            fact_refs,
        ))
    return found


def _deferral_findings(path, value, fact_refs, fact_kinds, own_work_ref):
    deferral, found = _object(
        path, value, DEFERRAL_FIELDS, ('reason', 'supporting_fact_refs'),
    )
    if deferral is None:
        return found
    if deferral.get('reason') is not None:
        found.extend(_text_findings(
            _join(path, 'reason'), deferral['reason'],
            max_bytes=DEFERRAL_TEXT_MAX_BYTES,
        ))
    if deferral.get('resume_condition') is not None:
        found.extend(_text_findings(
            _join(path, 'resume_condition'), deferral['resume_condition'],
            max_bytes=DEFERRAL_TEXT_MAX_BYTES,
        ))
    if deferral.get('resume_after') is not None:
        found.extend(_timestamp_findings(_join(path, 'resume_after'), deferral['resume_after']))
    origin = deferral.get('origin_work_ref')
    if origin is not None:
        problems = _token_findings(_join(path, 'origin_work_ref'), origin, LOCAL_REF)
        if not problems and origin == own_work_ref:
            problems.append(Finding(_join(path, 'origin_work_ref'), 'self_reference'))
        found.extend(problems)
    supporting = deferral.get('supporting_fact_refs')
    if supporting is not None:
        problems = _supporting_findings(
            _join(path, 'supporting_fact_refs'), supporting, fact_refs,
        )
        found.extend(problems)
        if not problems and not any(
            fact_kinds.get(ref) == 'explicit_deferral' for ref in supporting
        ):
            found.append(Finding(
                _join(path, 'supporting_fact_refs'),
                'deferral_requires_deferred_fact',
            ))
    return found


def validate_update(value) -> list:
    """Every structural finding for one parsed candidate, bounded."""

    envelope, found = _object(
        '$', value, ENVELOPE_FIELDS,
        ('schema', 'project_label', 'update_ref', 'stream_ref', 'sequence',
         'works', 'reporter_version', 'privacy_policy_version'),
    )
    if envelope is None:
        return found
    if envelope.get('schema') is not None and envelope['schema'] != SCHEMA:
        found.append(Finding('schema', 'not_allowed'))
    if envelope.get('project_label') is not None:
        found.extend(_text_findings(
            'project_label', envelope['project_label'],
            max_chars=PROJECT_LABEL_MAX_CHARS,
        ))
    for key in ('update_ref', 'stream_ref'):
        if envelope.get(key) is not None:
            found.extend(_token_findings(key, envelope[key], RANDOM_REF))
    sequence = envelope.get('sequence')
    if sequence is not None:
        if isinstance(sequence, bool) or not isinstance(sequence, int):
            found.append(Finding('sequence', 'wrong_type'))
        elif not 1 <= sequence <= MAX_SEQUENCE:
            found.append(Finding('sequence', 'out_of_range'))
    for key in ('reporter_version', 'privacy_policy_version'):
        if envelope.get(key) is not None:
            found.extend(_token_findings(key, envelope[key], VERSION_TEXT))
    history = False
    if envelope.get('origin') is not None:
        problems = _enum_findings('origin', envelope['origin'], ORIGINS)
        found.extend(problems)
        history = not problems and envelope['origin'] == 'history_import'
    if envelope.get('session_complete') is not None:
        if not isinstance(envelope['session_complete'], bool):
            found.append(Finding('session_complete', 'wrong_type'))
        elif not history:
            found.append(Finding('session_complete', 'history_import_only'))
    if envelope.get('works') is not None:
        items, problems = _list('works', envelope['works'], maximum=MAX_WORKS, minimum=1)
        found.extend(problems)
        refs = set()
        for index, item in enumerate(items or ()):
            item_path = f'works[{index}]'
            found.extend(_work_findings(item_path, item))
            ref = item.get('work_ref') if isinstance(item, dict) else None
            if isinstance(ref, str) and LOCAL_REF.fullmatch(ref):
                if ref in refs:
                    found.append(Finding(_join(item_path, 'work_ref'), 'duplicate'))
                refs.add(ref)
            facts = item.get('facts') if isinstance(item, dict) else None
            if history and isinstance(facts, list):
                found.extend(
                    Finding(f'{item_path}.facts[{position}].occurred_at',
                            'required_for_history_import')
                    for position, fact in enumerate(facts)
                    if isinstance(fact, dict) and fact.get('occurred_at') is None
                )
    if not found:
        try:
            size = len(canonical_bytes(envelope))
        except (TypeError, ValueError):
            found.append(Finding('$', 'invalid_unicode'))
        else:
            if size > MAX_UPDATE_BYTES:
                found.append(Finding('$', 'update_too_large'))
    return _bounded(found)


def _bounded(found) -> list:
    unique = []
    for item in found:
        if item not in unique:
            unique.append(item)
    return unique[:MAX_FINDINGS]


# ── Credential and private-path scan ──────────────────────────────────────

_PROVIDER_KEYS = tuple(re.compile(pattern) for pattern in (
    r'\b(?:AKIA|ASIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|APKA)[0-9A-Z]{16}\b',
    r'\bgh[pousr]_[A-Za-z0-9]{36,255}\b',
    r'\bgithub_pat_[A-Za-z0-9_]{22,255}\b',
    r'\bglpat-[A-Za-z0-9_-]{20,}',
    r'\bsk-(?:ant-|proj-|svcacct-|admin-)?[A-Za-z0-9_-]{20,}',
    r'\bxox[abposre]-[A-Za-z0-9-]{10,}',
    r'\b(?:sk|rk|pk|whsec)_(?:live|test)_[A-Za-z0-9]{16,}',
    r'\bwhsec_[A-Za-z0-9]{24,}',
    r'\bAIza[0-9A-Za-z_-]{35}',
    r'\bGOCSPX-[A-Za-z0-9_-]{20,}',
    r'\bya29\.[A-Za-z0-9_-]{20,}',
    r'\bnpm_[A-Za-z0-9]{36}\b',
    r'\bpypi-[A-Za-z0-9_-]{50,}',
    r'\bhf_[A-Za-z0-9]{30,}\b',
    r'\bSG\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}',
    r'\bSK[0-9a-f]{32}\b',
    r'\bdo[opr]_v1_[a-f0-9]{64}\b',
    r'\bshp(?:at|ca|pa|ss)_[a-fA-F0-9]{32}\b',
    r'\bkey-[0-9a-f]{32}\b',
    r'\bAccountKey=[A-Za-z0-9+/=]{20,}',
    r'\b(?:SharedAccessSignature|SharedAccessKey)=[A-Za-z0-9+/=%]{20,}',
    r'\b(?:sq0atp|sq0csp|EAAA)[A-Za-z0-9_-]{20,}',
    r'\bdckr_pat_[A-Za-z0-9_-]{20,}',
    r'\b(?:lin|linear)_(?:api|oauth)_[A-Za-z0-9]{20,}',
    r'\bsecret_[A-Za-z0-9]{40,}',
    r'\bntn_[A-Za-z0-9]{40,}',
))
_PRIVATE_KEY = re.compile(
    r'-----BEGIN [A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----|PuTTY-User-Key-File-'
)
_AUTHORIZATION = (
    re.compile(
        r'(?i)\bauthorization\s*[:=]\s*(?:bearer|basic|token|digest)?\s*'
        r'[A-Za-z0-9._~+/-]{8,}=*'
    ),
    re.compile(r'(?i)\bbearer\s+[A-Za-z0-9._~+/-]{16,}=*'),
)
_BASIC = re.compile(r'(?i)\bbasic\s+([A-Za-z0-9+/]{12,}={0,2})(?![A-Za-z0-9+/=])')
_JWT = re.compile(
    r'\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}'
)
_ASSIGNMENT = re.compile(
    r'(?i)(?<![a-z0-9])'
    r'(?:pass(?:word|wd|phrase)?|pwd|secret(?:[_-]?key)?|client[_-]?secret|'
    r'api[_-]?key|apikey|access[_-]?(?:key|token)|refresh[_-]?token|'
    r'auth[_-]?token|id[_-]?token|session[_-]?(?:key|token|secret)|'
    r'private[_-]?key|bearer[_-]?token|x-api-key|token|cookie|'
    r'credentials?)'
    r'["\']?\s*(?:=|:|=>|->)\s*(?P<quote>["\']?)'
    r'(?P<value>[^\s"\'`,;)\]}]{4,})'
)
_PLACEHOLDER = re.compile(
    r'(?i)^(?:<[^>]*>|\$\{?[a-z_][a-z0-9_]*\}?|\{\{.*\}\}|x{3,}|\*{3,}|'
    r'\.{3,}|redacted|\[redacted\]|none|null|nil|true|false|undefined|'
    r'required|optional|string|str|bytes|text|secret|password|token|'
    r'example|placeholder|changeme|your[_-].*|my[_-].*|'
    r'[a-z_][a-z0-9_.]*\(.*|(?:os|process|settings|config|env|self|'
    r'request|ctx)\..*)$'
)
_URL = re.compile(r'(?i)\b[a-z][a-z0-9+.-]{1,15}://[^\s<>"\'`]+')
_BARE_CREDENTIALS = re.compile(
    r'(?<![\w/@.:-])[A-Za-z0-9._%+-]{1,64}:[^\s@/:]{6,}@'
    r'[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+'
)
_SENSITIVE_PARAMETER = re.compile(
    r'(?i)^(?:access_?token|id_?token|refresh_?token|token|auth_?token|'
    r'api_?key|apikey|key|secret|client_?secret|password|passwd|pwd|sig|'
    r'signature|x-amz-signature|x-amz-credential|x-amz-security-token|'
    r'x-goog-signature|x-goog-credential|auth|authorization|code|session|'
    r'session_?id|sessionid|sid|jwt|bearer|private_?token|ticket)$'
)
_WEBHOOK_HOSTS = (
    ('hooks.slack.com', '/services/'),
    ('discord.com', '/api/webhooks/'),
    ('discordapp.com', '/api/webhooks/'),
    ('outlook.office.com', '/webhook'),
)
_OPAQUE = re.compile(r'[A-Za-z0-9+/=_-]{32,}')
_LOCAL_PATH = (
    re.compile(
        r'(?<![A-Za-z0-9_.-])/(?:Users|home|root)/[^\s"\'`/]+'
        r'|(?<![A-Za-z0-9_.-])/(?:private/var|var/folders|private/tmp)/'
    ),
    re.compile(r'(?i)(?<![A-Za-z0-9])[a-z]:\\(?:users|documents and settings)\\'),
    re.compile(r'~[/\\]\.(?:claude|codex)(?:[/\\]|\b)'),
)


def _assignment_is_secret(match) -> bool:
    value = match.group('value').rstrip('.')
    if _PLACEHOLDER.match(value):
        return False
    if match.group('quote'):
        return len(value) >= 6
    has_digit = any(char.isdigit() for char in value)
    mixed_case = (
        any(char.isupper() for char in value)
        and any(char.islower() for char in value)
    )
    symbol = any(char in '_-+/=.~!@#$%^&*' for char in value)
    return (len(value) >= 6 and has_digit) or (
        len(value) >= 8 and (mixed_case or symbol)
    )


def _url_findings(url: str) -> set:
    codes = set()
    trimmed = url.rstrip('.,;:)]}')
    try:
        parts = urlsplit(trimmed)
        host = (parts.hostname or '').lower()
    except ValueError:
        return codes
    if '@' in parts.netloc:
        userinfo = parts.netloc.rsplit('@', 1)[0]
        user, _separator, password = userinfo.partition(':')
        if password or parts.scheme.lower() in ('http', 'https') or (
            user and user.lower() not in ('git', 'ssh', 'hg', 'svn')
        ):
            codes.add('secret.credential_url')
    for part in (parts.query, parts.fragment):
        if '=' not in part:
            continue
        for key, item in parse_qsl(part, keep_blank_values=True):
            if item and _SENSITIVE_PARAMETER.match(key.strip()):
                codes.add('secret.sensitive_url_parameter')
    path = parts.path or ''
    for webhook_host, prefix in _WEBHOOK_HOSTS:
        if (host == webhook_host or host.endswith('.' + webhook_host)) and (
            path.startswith(prefix)
        ):
            codes.add('secret.webhook_url')
    if host.endswith('.webhook.office.com'):
        codes.add('secret.webhook_url')
    return codes


def _opaque(run: str) -> bool:
    if all(char in '0123456789abcdef' for char in run.lower()) and (
        run == run.lower() or run == run.upper()
    ):
        return False
    upper = any(char.isupper() for char in run)
    lower = any(char.islower() for char in run)
    digit = any(char.isdigit() for char in run)
    return (upper and lower and digit) or len(run) >= 120


def scan_text(value: str) -> set:
    """Reason codes for one string; never the matched text."""

    text = unicodedata.normalize('NFKC', value)
    codes = set()
    if _PRIVATE_KEY.search(text):
        codes.add('secret.private_key')
    if any(pattern.search(text) for pattern in _PROVIDER_KEYS):
        codes.add('secret.provider_key')
    if any(pattern.search(text) for pattern in _AUTHORIZATION):
        codes.add('secret.authorization')
    for match in _BASIC.finditer(text):
        token = match.group(1)
        if any(char.isdigit() for char in token) or token.endswith('=') or (
            '+' in token or '/' in token
        ):
            codes.add('secret.authorization')
    if _JWT.search(text):
        codes.add('secret.jwt')
    if any(_assignment_is_secret(match) for match in _ASSIGNMENT.finditer(text)):
        codes.add('secret.sensitive_assignment')
    for match in _URL.finditer(text):
        codes |= _url_findings(match.group(0))
    if _BARE_CREDENTIALS.search(text):
        codes.add('secret.credential_url')
    if any(_opaque(match.group(0)) for match in _OPAQUE.finditer(text)):
        codes.add('secret.opaque_blob')
    if any(pattern.search(text) for pattern in _LOCAL_PATH):
        codes.add('privacy.local_path')
    return codes


def _walk_strings(value, path='$'):
    if isinstance(value, dict):
        for key in sorted(value, key=str):
            name = key if key in PATH_NAMES else UNKNOWN_KEY
            yield from _walk_strings(value[key], _join(path, name))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_strings(item, f'{path}[{index}]')
    elif isinstance(value, str):
        yield path, value


def scan_update(value) -> list:
    """Credential and private-path findings for every string field."""

    found = []
    for path, text in _walk_strings(value):
        try:
            codes = scan_text(text)
        except (ValueError, TypeError):
            codes = {'invalid_unicode'}
        found.extend(Finding(path, code) for code in sorted(codes))
    return _bounded(found)


# ── One entry point for the skill and for Oira ────────────────────────────


def prepare(raw) -> dict:
    """Return ``{'ok': True, 'canonical': ...}`` or bounded refusals."""

    try:
        candidate = load_candidate(raw)
    except CandidateRefused as exc:
        return {'ok': False, 'errors': [item.wire() for item in exc.findings]}
    found = _bounded([*validate_update(candidate), *scan_update(candidate)])
    if found:
        return {'ok': False, 'errors': [item.wire() for item in found]}
    return {'ok': True, 'canonical': canonical_json(candidate)}


def history_stream_ref(session_id: str) -> str:
    """The stream reference of one past session (see the module docstring)."""

    digest = hashlib.sha256(
        b'oira_history_stream.v1\x00' + session_id.encode('utf-8'),
    ).digest()
    return str(uuid.UUID(bytes=digest[:16], version=4))


def _session_id(value: str) -> bool:
    return 0 < len(value) <= 255 and value.isprintable() and value == value.strip()


def _write(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, separators=(',', ':')) + '\n')


def main(argv=None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        if sys.version_info < MINIMUM_PYTHON:
            _write({'ok': False, 'errors': [
                {'path': '$', 'code': 'python_version_unsupported'},
            ]})
            return 3
        if arguments == ['--new-ref']:
            sys.stdout.write(str(uuid.uuid4()) + '\n')
            return 0
        if (
            len(arguments) == 2 and arguments[0] == '--history-stream'
            and _session_id(arguments[1])
        ):
            sys.stdout.write(history_stream_ref(arguments[1]) + '\n')
            return 0
        if arguments:
            _write({'ok': False, 'errors': [{'path': '$', 'code': 'not_allowed'}]})
            return 2
        raw = sys.stdin.buffer.read(MAX_RAW_INPUT_BYTES + 1)
        result = prepare(raw)
        if result['ok']:
            sys.stdout.write(result['canonical'] + '\n')
            return 0
        _write(result)
        return 2
    except Exception:  # noqa: BLE001 - fail closed without echoing input
        _write({'ok': False, 'errors': [
            {'path': '$', 'code': 'preflight_internal_error'},
        ]})
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
