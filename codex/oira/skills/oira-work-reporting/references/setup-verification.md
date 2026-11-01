# Complete and verify setup

Setup is a resumable workflow, not work to report. Preserve the chosen transport,
installation owner, company/project and reporting preference across restarts.
An installed package, browser grant or user saying “done” alone proves neither
hook execution nor work capture. Never manufacture hook events or work facts.

Use the available native question/options tool for required choices in the ongoing
chat. Codex exposes `request_user_input_async` in supported desktop sessions;
use `request_user_input` only when actually available in the current mode.
Claude may expose `AskUserQuestion`. Keep the choice pending instead of ending
with a final-text question. Do not switch modes or invent tools. A host without
a choice tool needs one concise text question and an explicit answer.

## Exclude the setup chat

Before enabling automatic reporting, run the installed hook helper with
`--app codex --environment production exclude-session --session-id
<actual native session ID>`. The ID must come from the current host, not a
transcript scan, another chat or a made-up UUID. Confirm `work_reporting=excluded`
using `session-status --session-id <same ID>`. An unavailable identity/helper
keeps automatic setup pending. Repeat this in any setup/verification continuation
chat. Never exclude the whole project or other working chats.

The local exclusion survives completion, disable/re-enable, reload and upgrade.
It stores only a hashed session identity and technical lifecycle fields, never
content. Ordinary reporting reminders are suppressed for that chat. Real native
hook observations can still verify installation locally and the non-work setup
acknowledgment can still be sent; neither creates Work. Do not submit a work
update or include an excluded chat in history import, even if reporting was
previously enabled. Never promise that installation will remove the saved key
from the chat. If this chat is later used for actual coding, direct the user to
a separate working chat so installation history stays excluded.

## Select the source

Read this agent's manifest from the official `oira-ai/plugins` public repository
and refreshed native directory metadata where available. Compare numeric SemVer
and required capabilities, not a lexical version string or the Oira CLI version.
Record the selected package version and fetched commit. An unpublished checkout
is not a public release. An empty search is not proof that a listing is absent.
Keep a newer compatible owned installation; inspect before refreshing/updating.
An explicit development recipe instead uses its specified local candidate
manifest and isolated development names/origin. It does not require a public
package to have been released and must never substitute the production package.

Codex's public listing was observed at 0.7.0 on 1 November 2026. That is historical
evidence, not a current latest-version guarantee. Current public-directory rules
exclude bundled lifecycle hooks, so local Codex automatic reporting uses the
complete repository package. Directory installation remains an alternative for
compatible on-request reporting/authentication. A key installation uses the
complete vault-backed native package where supported, not a duplicate skill.

Use a persistent user-folder install outside the code repository. Only the
explicit current folder/project binding enables reporting. For Kiro/custom
profiles or another host requiring project-local assets, preserve configuration
and add only the personal generated paths to Git's local info/exclude. Change
shared .gitignore only deliberately; verify ignored files and never put a key
in a repository. Do not enroll other folders because a plugin is global.

## Native hook checkpoint (local Codex/Claude automatic reporting)

1. Exclude this setup session as above. Verify the complete plugin is installed/enabled, its three hook definitions
   are discovered, the selected vault/native OAuth transport works, the exact
   target is authorized, and canonical local preflight passes. Save the exact
   enabled binding using the existing documented helper. Hooks remain local,
   credential-free and network-free.
2. Generate one fresh UUID `check_ref`. Use the installed helper, private Python
   or validated current runtime: `--app codex --environment production
   verify-begin --project-root <exact folder> --check-ref <UUID>`. Keep this
   reference through lost responses/reloads. Use the interpreter/helper from the
   registered native hook command, including its cached package path; do not mix
   Python runtimes. These commands must actually be supported; an old runtime
   without them needs an explicit update/repair.
3. Ask the user to open native **Hooks**, review/trust the exact Oira
   SessionStart, UserPromptSubmit and Stop definitions, then reply **done**.
   Wait. In Codex CLI use `/hooks`; guide the current native UI otherwise.
   Never write trust hashes, bypass review or approve it on the user's behalf.
   Reuse existing trust only after verifying the exact definitions are unchanged.
4. If native loading requires a reload/new chat, guide that action; do not restart
   the app yourself. Give the continuation prompt with this check reference and
   folder. The existing enabled binding/check survives the new chat. A fresh
   SessionStart and the next UserPromptSubmit must come from the real host.
   The continuation must explicitly say this is a verification-only chat and
   run `exclude-session` for its actual new session ID before any work path.
5. After the user's confirmation, repeat `verify-begin` with the same arguments
   and `--review-confirmed`. This records the user's confirmation, not a native
   trust attestation. Read `verify-status --project-root <folder> --check-ref
   <UUID> --session-id <current native session from the hook reminder>`.
   Status is read-only: it neither creates state nor simulates a hook. Require
   all three observations for this fresh check in the same current session and
   current turn. A reload of that session requires fresh prompt/Stop observations.
   Inspect native trust/discovery through supported tools or UI when accessible;
   if trust cannot be independently read, label it user-confirmed explicitly.
6. Stop executes after a response. Its first invocation in each resumed verification
   session after review confirmation
   can request one bounded continuation to finish setup, even after an ordinary
   no-change checkpoint. Follow that continuation, re-read status and finish the
   normal current nonce checkpoint. Never call `event` yourself to pass this test.
   If a hook is missing, explain the exact pending reload/repair once and resume
   after it. Do not loop or claim full automatic readiness. Observations are local
   diagnostics, not cryptographic/native process attestation.

For updates only on request, hooks are not required. For other/unqualified hosts,
verify the supported personal-instruction route and state that native automatic
hooks were not verified. Do not run Codex/Claude helper commands on those hosts.

## Installation during ongoing work

An ordinary working chat may first emit UserPromptSubmit or Stop after install.
The helper records that first observed event as late attachment; it never
manufactures SessionStart or counts that marker as native verification. Declare
the actual work identity/context at sequence 1 before progress/results, in the
same canonical update, so capture/processing sees a complete declaration before
its facts. Include only known material facts with honest timestamps; no empty
start update, invented earlier activity or automatic transcript import. If a
stream exists, recover status and continue its sequence instead of declaring
another stream merely because the hook was missing. Repeated Stop is bounded to
one reminder per open turn. Resume/reload keeps the exclusion and first-observed
marker; a later real SessionStart does not rewrite earlier observation history.
Changed destinations require a fresh context; disabled/revoked access never
gets repaired by switching projects, replaying old facts or inventing a start.

## Oira acknowledgment

Call `oira_verify_setup(check_ref=<same UUID>, expected_target=<exact target>)`
through the selected Oira MCP transport. A fresh non-hook route also generates
one UUID. Require `schema=oira_setup_check.v1`, `result=accepted`, the same
reference and exact target. The server checks live reporting permission, active
project/resource epochs and paused capture under existing authority locks.
It retains only a bounded cache of diagnostic receipts on the connection.
Retained-reference retries return the original receipt; old entries can expire
from that cache. A changed target/authorization needs a new setup check.

A lost reply can be recovered through `oira_connection_status(expected_target)`
and its matching `setup_check`, or by retrying the same check. Never mark another
reference's/historical target's receipt as this check. An absent tool means the
server release is pending. Unavailable, rejected or paused is not success.

Read `reporting.capture` from connection status before calling the diagnostic.
It uses the full source-capture gate, including billing, company mode and pause,
not just the key/project grant. A denial's reason/action must be shown and resolved
through its ordinary owner. A working status call or processing admission cannot
prove that a new source write is allowed. Never change billing or company policy
silently, fabricate an acknowledgment or reinstall to bypass a capture refusal.

For the automatic hook route, save only this structured setup receipt to a
temporary file and call the same helper `verify-finish --project-root <folder>
--check-ref <UUID> --session-id <current session> --receipt-file <file>` after
fresh hook evidence and the acknowledgment match. Delete the file afterwards.
The local marker is explicitly host-reported; it is not independent server
verification. It stops setup-specific continuations in future chats. Polling
never marks setup complete. A changed helper/target invalidates old evidence;
an upgrade/new setup check uses a fresh reference. An invalidated helper/owner
cannot restart the same reference and reuse its old server acknowledgment.
Repeating an unchanged enabled binding preserves progress; disabling or changing
its exact target/installation resets it. A deliberate renewed review
confirmation can rearm one final check, without a background retry loop.

This check creates no work update, source revision, outbox/model job, question or
history import. It does not upload native event payloads, session identifiers,
paths, transcripts, files, credentials or prompt text. It does not attest hook
trust, context-read permission or actual work capture. The UI shows connection
acknowledgment and real work capture separately.

## Permission to send real work

Keep four checks distinct: Oira authentication/project authority, native hook
trust, coding-host approval to disclose work, and Oira's actual capture receipt.
Before enabling automatic updates, name the exact local folder and Oira
company/project and explain the structured work facts sent there. Obtain the
user's explicit reporting choice. Never infer this permission from installing a
plugin, a connected key, one available project or trusted hooks.

Honor existing scoped permission where the native host recognizes it. A saved
binding routes updates; it does not override the host's policy in a new chat.
Where fresh confirmation is required, ask once with the exact destination and
concrete proposed facts, and wait. A new-chat continuation should carry the
folder, company/project and setup reference, plus an explicit reporting request
for the user to review and paste themselves. Do not manufacture human permission
by writing a consent statement to a file or forwarding an agent message.

An approval denial means stop the send path. Explain the stated reason and that
no receipt was obtained. Do not minimize/reword the report, generate a new
reference, switch credentials/transports or call HTTP/CLI to get around it.
After explicit human approval of the actual payload, reuse its unchanged
reference and recover an uncertain attempt first. Approval of a brief alternative
does not authorize a previously rejected detailed performance/security report.
Never weaken approval policy or host trust. Record a blocked local checkpoint,
continue independent work and ask for the required human action once.

The non-work setup acknowledgment proves neither disclosure permission nor
actual work capture. Do not invent a test work item. The first genuine authorized
update and its exact captured receipt verify the reporting path; processing and
visible Work Items remain a further, separate check. Host/enterprise policies can
still require human approval even when the plugin and Oira consent are correct.

## Finish truthfully

Report installed source/version; authentication and exact project; hook discovery,
review confirmation and fresh execution (or on-request/unsupported); Oira setup
acknowledgment; optional context availability; first real work capture.
Hook/connection verification is complete only after the applicable hook checks
and Oira acknowledgment pass. The helper's complete state still reports native
send permission as verify_in_host and work capture as not_tested; do not label
automatic reporting verified from that state alone. Company-context reads require their own consent and actual
available query tools; they never silently enable reporting or interventions.

The first real work update remains pending until genuine work is reported through
canonical preflight and its receipt is recovered by `oira_work_update_status`.
Do not invent installation activity to turn that indicator green. Captured and
processed are separate states; parked processing can still accept work.
