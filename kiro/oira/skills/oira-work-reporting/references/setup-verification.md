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
`--app kiro --environment production exclude-session --session-id
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
explicit current folder binding, or the repository binding chosen under
[Git worktrees](#git-worktrees), enables reporting. For Kiro/custom
profiles or another host requiring project-local assets, preserve configuration
and add only the personal generated paths to Git's local info/exclude. Change
shared .gitignore only deliberately; verify ignored files and never put a key
in a repository. Do not enroll other folders because a plugin is global.

## Native hook checkpoint (local Codex/Claude automatic reporting)

1. Exclude this setup session as above. Verify the complete plugin is installed/enabled, its three hook definitions
   are discovered, the selected vault/native OAuth transport works, the exact
   target is authorized, and canonical local preflight passes. Ask the
   [Git worktrees](#git-worktrees) question, then save the exact enabled
   binding using the existing documented helper. Hooks remain local,
   credential-free and network-free.
2. Generate one fresh UUID `check_ref`. Use the installed helper, private Python
   or validated current runtime: `--app kiro --environment production
   verify-begin --project-root <exact folder> --check-ref <UUID>`. Keep this
   reference through lost responses/reloads. Use the interpreter/helper from the
   registered native hook command, including its cached package path; do not mix
   Python runtimes. These commands must actually be supported; an old runtime
   without them needs an explicit update/repair.
3. Follow the actual host's loading/review flow:
   - **Codex only:** ask the user to review/trust the exact Oira SessionStart,
     UserPromptSubmit and Stop definitions in the available native Hooks UI
     (CLI: `/hooks`), then reply **done**. Wait. Never write trust hashes, bypass
     review or approve it on the user's behalf. Reuse existing trust only after
     verifying the exact definitions are unchanged.
   - **Claude Code only:** hooks load automatically from an enabled plugin.
     There is no Codex Settings / Hooks enable/trust action. Inspect the installed
     definitions and effective configuration; `/hooks`, when available, is a
     read-only viewer. Check `disableAllHooks` and managed policy without changing
     policy. Once the user authorized automatic reporting and you reviewed the
     enabled configuration, continue without asking for a **done** reply. Guide
     only an actual workspace/plugin trust prompt or required reload shown by
     this host, and wait for that real user action when needed.
   Official references: [Codex hooks](https://learn.chatgpt.com/docs/hooks) and
   [Claude Code hooks](https://code.claude.com/docs/en/hooks).
4. If native loading requires a reload/new chat, guide that action; do not restart
   the app yourself. Give the continuation prompt with this check reference and
   folder. The existing enabled binding/check survives the new chat. A fresh
   SessionStart and the next UserPromptSubmit must come from the real host.
   The continuation must explicitly say this is a verification-only chat and
   run `exclude-session` for its actual new session ID before any work path.
5. After the applicable review in step 3, repeat `verify-begin` with the same arguments
   and `--review-confirmed`. For Codex this records the user's review confirmation;
   for Claude it records the local configuration review after automatic-reporting
   authorization. Neither is a native trust attestation. Read `verify-status --project-root <folder> --check-ref
   <UUID> --session-id <current native session from the hook reminder>`.
   Status is read-only: it neither creates state nor simulates a hook. Require
   all three observations for this fresh check in the same current session and
   current turn. A reload of that session requires fresh prompt/Stop observations.
   Inspect native trust/discovery through supported tools or UI when accessible;
   Label Codex trust user-confirmed when it cannot be independently read; for
   Claude report configured loading and observed execution separately.
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

## Git worktrees

An exact folder binding routes only that folder and its subfolders. A linked
Git worktree (Claude Code desktop `.claude/worktrees/*`, Codex worktrees,
`git worktree add`) has its own `.git` file, so its chats stay unbound unless
a repository binding exists. When the project folder is in a Git repository
and the user chooses automatic reporting, ask once whether it should also
cover this repository's git worktrees. Default to yes when this host creates
chat worktrees (Claude Code desktop, the Codex app) or `git worktree list`
shows others; otherwise default to the exact folder. An existing folder-only
binding has not answered this question: ask it on a repeated setup or update.

On yes, add `--inherit-repository` to the helper's `enable` command. It saves
one `repository:<common Git directory>` binding that the main checkout and
every linked worktree resolve to. An exact folder binding still takes
precedence where one exists, and a nested independent repository never
inherits it. Outside a Git checkout the helper refuses with
`git_repository_required`. On no, keep the exact folder binding. Name the
covered checkouts in the reporting authorization.

Confirm with `session-status --session-id <id> --project-root <folder>`. Its
`binding` object names `binding_key`, `scope` and `automatic_reporting` for
that folder; check an existing worktree the same way. `verify-status` returns
the same object. `automatic_reporting: unbound` with `unbound_reason:
other_checkout_bound` means another checkout of this repository is bound but
this one is not: tell the user rather than report from it.

## Resume browser-selected history

After browser authentication and project approval, call `oira_connection_status`
for the exact selected target again. For `history_import[project_label].state`
`requested`, `in_progress` or `incomplete`, start/resume "Import recent work" in
the installed skill now, before ending setup. Use `window_from` and `window_to`;
`max_days` is a compatibility calendar bound, not a billing cap or the
selected import period. Do not ask for a new history request or reset
the period. If the host requires additional permission, use its native question
tool with the approved target/window and wait. Honor denial. Only prior approved
project work is eligible; exclude setup/verification sessions before reading
bodies. Pending hook verification does not cancel import. Finish/recover through
the normal history tools and state the actual counts or precise blocker.

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

After reading fresh `oira_connection_status(expected_target=...)`, save its
`context.available` observation with the same exact local binding: append
`--context-reads available` or `--context-reads unavailable` to the existing
helper's `bind`/`enable` command (or the bundled `projects bind` command).
Do this only with a package that supports the option; upgrade older packages
normally instead of claiming the reminder was installed. This local Boolean
controls a short consultation reminder, not server permission. A changed target
or grant clears it. Every actual consultation still rechecks current consent.
No hook contacts Oira, composes questions or reads transcripts. Hosts without
these hooks use the skill's consultation triggers directly.

## Permission to send real work

Keep four checks distinct: Oira authentication/project authority, native hook
trust, coding-host approval to disclose work, and Oira's actual capture receipt.
Before enabling automatic updates, name the exact local folder (and, for a
repository binding, its git worktrees) and Oira company/project and explain
that structured implementation, test and deployment
facts go there at material milestones and before stopping, or only on request
if that is the chosen mode. Record the chosen mode in the exact local binding.
Reuse explicit authorization for that binding where the host recognizes it.
Exclude credentials, private keys, prompts, transcripts, raw tool output and
file contents. Pause immediately on request. Never infer this permission from installing a
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
Never weaken approval policy or host trust. Record a blocked local checkpoint with the original update reference,
continue independent work and ask for the required human action once.

The non-work setup acknowledgment proves neither disclosure permission nor
actual work capture. Do not invent a test work item. The first genuine authorized
update and its exact captured receipt verify the reporting path; processing and
visible Work Items remain a further, separate check. Host/enterprise policies can
still require human approval even when the plugin and Oira consent are correct.

## Finish truthfully

Report installed source/version; authentication and exact project; binding
scope (exact folder, or repository with its git worktrees); hook discovery,
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
