# Explicit company-context checks

The official key adapter allows up to 180 seconds per context submit or status
call, including reading a completed result under fresh permissions. A native
host can impose a shorter deadline. Keep the original request/check identity
after a transport timeout; poll that same request instead of submitting a new
question. Other key-backed operations keep their 30-second allowance.

Use this only after separate `memory_context:read` consent, and
`agent_interventions:receive` for scoped interventions. Existing reporting and
history-import consent grant neither. Valid OAuth scopes do not make them
defaults. `oira context enable` points to existing account/connection consent;
it never grants access locally. The native host must request the relevant
scopes and complete browser authorization. Keep its OAuth credentials host-owned.

## Questions that help the next decision

Include the intended outcome, relevant project or product scope, uncertain
assumptions and next decision. Use an existing returned work handle when useful.
Ask for accepted decisions and their evidence separately from proposals and
recent observations. Oira may return related work, constraints and conflicts;
absence of evidence is not proof that a requirement or dependency does not exist.

| Situation | Useful composed question | How to use the result |
| --- | --- | --- |
| Changing an API used by another team | Which accepted contracts and active consumer work govern this response format? I assume timestamps remain UTC; the next decision is whether a versioned endpoint is needed. | Preserve supported contracts; investigate uncovered consumers before changing the shared interface. |
| Catching up imported work while live updates continue | Which accepted latency, ordering and recovery requirements govern history imports and live updates in this project? The next decision is admission and retry behavior. | Separate product requirements from measured capacity; test the chosen policy locally. |
| Resuming a partly completed feature | What related work, accepted scope changes and unresolved decisions affect this outcome since the prior milestone? | Reconcile the plan and avoid duplicate or conflicting implementation. |
| Preparing a release | What accepted release constraints and unresolved dependencies apply to this change? | Treat the answer as evidence; deployment still needs the user's authorization. |

Do not ask Oira to approve every edit, run a local test or repeat facts already
settled by a current answer. It is not a substitute for inspecting code or logs.

## Reading an incomplete result

When reporting a consultation result, use a short evidence-to-action statement:
what the current answer establishes (with its reference), its missing coverage,
and the next action that follows. For example: "The accepted contract requires
UTC timestamps [returned reference]. Consumer migration requirements were not
covered, so the format change remains on hold. I will inspect the existing
serialization and its callers next." Do not turn a missing dependency into
speculative implementation options, new fields, a compatibility plan or a
requirements checklist. Only propose those when the task and evidence support
that decision. With no callable tool or denied consent, simply identify that
limitation, the dependent decision on hold and any useful independent inspection.
When a complete current answer resolves the dependency, act on it within the
user's existing authorization instead of asking for the same decision again.

Only `release_state=current` permits using the returned evidence. Also inspect
the answer status, coverage and degradation codes; current does not mean complete.

- `bounded_canonical_selection`, `bounded_catalog_selection` or
  `bounded_plan_execution`: the query covered a bounded subset. Retain useful
  cited evidence, identify the missing scope and deliberately narrow a follow-up
  if that scope is needed for the decision. Do not claim an exhaustive search.
- A capacity/deadline or temporarily-unavailable response means processing or
  verification could not finish now. Follow the returned retry/poll guidance;
  it says nothing about whether the company has evidence. Poll a pending check
  with the same IDs, including after a local restart.
- `no_matching_evidence`: this permitted query found no matching evidence.
  State the gap; do not translate it into "nothing exists" or invent approval.
- Stale, withheld or revoked results cannot be used. Follow the typed recovery
  action under the original target; never widen access or switch credentials.
- A failed terminal job needs its returned recovery action. Repeated status
  reads do not restart it. A deliberate new question/recheck uses a higher intent
  revision for the same operation, without disguising a failed original attempt.

For a conflict or uncovered consequential dependency, hold that affected step
and continue unrelated authorized work. A human decision must come from the
existing decision owner. Displaying or acknowledging an intervention is not a
resolution and never proves that the host stopped execution.

## Durable check workflow

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
   Wire bounds count compact UTF-8 JSON: 64 KiB per request and 128 KiB per
   response, including international text. Local reporting digests retain
   their established encoding.
   Explicit input files have a separate 256 KiB raw acquisition cap to bound
   parsing. Escapes and formatting within that cap are accepted when the
   parsed request still fits the same 64 KiB compact wire bound.
   Never put credentials in questions, files or command arguments.
   The question can contain 12,000 characters; assumptions are at most sixteen
   strings of 1,000 characters, and the next step at most 4,000 characters.
   Their composed engine intent, including headings, must fit 16,000 characters.
   Compose the actual question; do not attach a chat transcript or source files.
   Optional `work_handle` is the exact `wh_...` returned by reporting or recent
   work status. It relates this private dialogue to already matched shared work
   and grants no access. Keep it stable for the operation. An unmatched report
   can still be queried without manufacturing a Work Item.
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
   Save the request UUID, check UUID, binding/generation, operation and revision
   in this task's notes; the same identifiers recover progress after a restart.
   Processing may take several minutes. Follow `poll_after_ms` (normally 5–30
   seconds), with a little jitter, while continuing independent authorized work.
   A local wait timeout does not cancel the server job. Poll that same check on
   resume; do not resubmit with a new UUID to get a faster answer. Submission
   acknowledges durable acceptance without waiting for inference. Retrieving a
   completed result can take longer while Oira validates current source access.
   A transport timeout does not establish whether a submit was captured; recover
   through status with the original request/check identity before any retry.
   `discussion_ref` and `message_ref` identify the visible private conversation;
   released results also include original artifact references. Oira shows the
   question as your coding agent's message and makes its answer available there
   through the same current source-permission checks.
   Set `include_discussion_refs: true` in direct submit/status calls to opt into
   the expanded response with discussion/artifact references and up to 128 KiB.
   Omitted/false retains the original closed v1 response fields and 32 KiB bound
   for older clients. This presentation option grants no execution allowance.
   The updated CLI sets it for composed questions; a full explicit request DTO
   keeps its exact supplied bytes.
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

## Direct MCP example

Use the host's actual MCP tool calls. In the example below `target` is the
complete frozen `expected_target` from approved connection status; `binding`
and `check` are the actual tool responses. Create fresh UUIDs for this task
once and retain them across lost-response retries. Replace the sample work
handle with your real report handle, or omit it when no report exists.

```javascript
const binding = await oira_bind_context_session({request: {
  expected_target: target,
  client_binding_ref: "c7565194-34de-43fe-858e-534096fd20af",
  local_context_nonce: "432297a1-4b54-4755-a3d8-0ec626669e97",
  adapter_id: "codex", adapter_version: "0.12.0"
}});
const check = await oira_check_context({request: {
  expected_target: target,
  session_binding_ref: binding.session_binding_ref,
  binding_generation: binding.binding_generation,
  client_request_ref: "f5ccf613-9482-4dfb-92f9-e6c89f749709",
  operation_ref: "portal-api-contract", intent_revision: 1,
  purpose: "change_consistency",
  work_handle: "wh_aaaaaaaaaaaaaaaaaaaaaaaaaa",
  question: "Before implementing the portal API, which accepted company decisions, product constraints and related team work govern its data contract? Validate the assumptions and identify conflicts or missing evidence.",
  assumptions: ["The producer contract remains authoritative.",
    "A change in timestamp units may affect another team's consumer."],
  next_step: "Implement the API mapping after checking the governing contract.",
  wait_ms: 0, include_discussion_refs: true
}});
// After check.poll_after_ms, read the SAME check. This starts no reasoning.
const status = await oira_context_check_status({request: {
  expected_target: target,
  session_binding_ref: binding.session_binding_ref,
  binding_generation: binding.binding_generation,
  check_ref: check.check_ref, include_discussion_refs: true
}});
```

Consume `status.result` only when `release_state` is `current`. Read its status,
facts/assessment, evidence, accepted baselines, alternatives, coverage,
degradation and conflicts together. `incomplete` means the evidence cannot
settle the question; `blocked` requires the existing decision-owner route.
Record what changed in the implementation plan and cite the relevant returned
references in your work facts. At a dependent milestone, use the same operation
and purpose with a higher revision and a new request UUID for a deliberately
updated question. A server can spend several minutes processing; never turn a
poll timeout, source gap or delayed reply into approval.

All commands accept the existing app/environment/folder/session selectors.
`--request-file` accepts only an explicit bounded closed DTO. The existing
reporting hooks remain local, credential-free and network-free; a Stop reminder
is not a host hold. Kiro and other unqualified hosts retain explicit advisory
request/status instructions and no guaranteed control. No new dashboard, noisy
feed, transcript import, worker fleet or background OAuth poller is introduced.
