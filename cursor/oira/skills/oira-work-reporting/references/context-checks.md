# Explicit company-context checks

Use this only after separate `memory_context:read` consent, and
`agent_interventions:receive` for scoped interventions. Existing reporting and
history-import consent grant neither. Valid OAuth scopes do not make them
defaults. `oira context enable` points to existing account/connection consent;
it never grants access locally. The native host must request the relevant
scopes and complete browser authorization. Keep its OAuth credentials host-owned.

1. Freeze this chat's exact `oira_coding_target.v1` from its existing explicit
   project/folder/session binding. Never select company by label, cwd, repo
   name or list order. Reconnect, fork, target-generation change or a fresh
   company context needs its own authenticated binding.
   Every CLI context command requires an explicit `--session <chat-id>` and
   shares reporting's immutable chat destination. Rebinding a folder cannot
   change the company of an already loaded chat; use a fresh chat/session.
   A context binding or receipt never creates or resets a reporting turn.
2. Use `oira_bind_context_session(request=...)`, retaining the returned opaque
   `session_binding_ref` and `binding_generation`. This is authenticated logical
   correlation, not proof of native process control. Use the schemas in
   `context-contracts.json`. A bundled launcher exposes `context bind`; native
   mode prints the exact operation/arguments with `sent=false`. Invoke those
   arguments through the host's native MCP tools. An optional
   `context bind --receipt-file <explicit host receipt JSON>` records identifiers
   as `host_reported`, never server-verified. For an expired/revoked logical
   binding, explicitly use `context bind --new-binding --client-binding-ref
   <new UUID>`; keep that UUID on lost-response retries. This never revives the
   old binding or clears its independent operation blocks.
3. At a meaningful plan/dependency/contract decision, before a consequential
   shared change, or after an explicit recheck request, compose one bounded
   question and assumptions about the tracked operation. Use the same
   `operation_ref`, immutable purpose and increasing `intent_revision` for
   deliberate rechecks. Do not read session-history files, attach raw hook
   events or infer a question from captured prompts. No check on every token,
   tool call or timer. Prefetch by submitting once and polling that check.
4. Call `oira_check_context(request=...)`. A typical bundled command is
   `oira --app codex context check --folder <folder> --session <session>
   --session-binding-ref <UUID> --binding-generation 1 --operation-ref <opaque>
   --intent-revision 1 --question-file <explicit JSON>`. That JSON can contain
   `{"question":"Which accepted company constraints govern this change?",
   "assumptions":["The existing contract remains authoritative."]}`. The local
   preflight consumes the generated server schema and the server revalidates
   all authority. An existing full closed DTO can be passed as `--request-file`.
   Wire bounds count compact UTF-8 JSON: 16 KiB per request and 32 KiB per
   response, including international text. Local reporting digests retain
   their established encoding.
   Explicit input files have a separate 64 KiB raw acquisition cap to bound
   parsing. Escapes and formatting within that cap are accepted when the
   parsed request still fits the same 16 KiB compact wire bound.
   Never put credentials in questions, files or command arguments.
   The composed question, assumptions and next step must fit 4,000 characters.
   Optional evidence hints are at most sixteen explicit `record:<UUID>`,
   `domain:<UUID>`, `subject:<UUID>` or `artifact:<UUID>` references using
   lowercase canonical UUIDs. They select candidates and grant no access.
5. Retain exact request/check IDs. API-key mode invokes existing hosted MCP;
   native mode only prints typed host-tool arguments. Neither substitutes its
   credential for the other. Lost-response retry of the same operation/revision
   must use the same question/request bytes; the local store retains correlation
   IDs/digest only. It never stores question/result bodies. Changed content
   requires a higher revision; never silently make a replacement request UUID.
6. `oira_context_check_status` / `context status --check-ref <UUID>` reads the
   original durable progress. Status polling never starts reasoning. Respect
   the returned poll delay and do not loop noisily. A completed result is
   usable only when `release_state=current`; source, permission and currentness
   can invalidate it before presentation expiry. Incomplete, pending, stale,
   unavailable and unsupported are never approval to proceed.
7. Hold the affected operation cooperatively while a consequential check is
   blocked or unavailable. Unrelated operations retain their own identity.
   `oira_context_interventions` / `context interventions` is a bounded scoped
   mailbox; `oira_ack_context_intervention` / `context ack` records received,
   displayed, agent_claimed_hold, declined, unsupported or failed observations.
   A sent/displayed message never proves an agent stopped. Synchronous denial,
   observed host-boundary hold, already-running interruption and automatic
   resume are unsupported in this integration. Never acknowledge
   `host_boundary_held` or claim `applied=true`.
8. Human questions use the existing private Brain question/conversation route;
   optional Slack delivery needs its existing authorized destination. Human
   response and receipt acknowledgment cannot clear a conflict. After original
   accepted resolution, request a higher intent revision and current recheck;
   the server's operation block remains until verified. Do not resume by
   interpreting a delivery as an executable command.
9. `oira_cancel_context_check` / `context cancel --check-ref <UUID>
   --check-generation <generation>` cancels the exact job. It does not clear an
   independent conflict block. `oira_revoke_context_session` / `context revoke`
   revokes the exact logical binding without claiming process interruption.

All commands accept the existing app/environment/folder/session selectors.
`--request-file` accepts only an explicit bounded closed DTO. The existing
reporting hooks remain local, credential-free and network-free; a Stop reminder
is not a host hold. Kiro and other unqualified hosts retain explicit advisory
request/status instructions and no guaranteed control. No new dashboard, noisy
feed, transcript import, worker fleet or background OAuth poller is introduced.
