---
name: oira-work-reporting
description: Keep Oira updated on the user's coding work when they ask, as structured work updates (decisions, progress, verification, blockers, questions, next steps and explicitly deferred work) for an approved project, and import the recent work of past sessions when the member approved it. Sends no transcripts, prompts, replies, tool output or files.
---

# Oira work reporting

Four Oira tools: `oira_connection_status`, `oira_submit_work_update`,
`oira_work_update_status` and `oira_finish_history_import`. Report only when
the user asks you to keep Oira updated, for the current task or for the
approved project (their own instruction from "Set up Oira" is that ask, for
the repository it names), or asks for a progress update or a handoff;
import past work only as "Import recent work" says. Codex and Claude can also
use explicitly enabled local hooks to remind you
to report new work facts automatically. Hook input and transcripts are never
uploaded. Other apps keep their instruction-based reporting.

For the user's authorized current work, declare each distinct intended outcome
once and report only material new facts afterward. Keep work references
stable. Preserve adopted and reversed decisions, implementation, verification,
blockers, questions, accepted next actions, scope boundaries, and relevant
interface, transformation, revision and environment facts. Separate explicit
deferred work into its own declaration so Oira can retain it as upcoming work.
An unfinished task is not automatically deferred. Distinguish proposed,
accepted, attempted, implemented, tested, committed, merged and released.
Report the check and its actual result without logs. Describe uncertainty
rather than filling missing facts. Never export prompts, replies,
conversation summaries, tool traffic, files, reasoning, or credentials, and
read past sessions only for an approved history import. Run the local
outbound preflight on the exact payload before transmission; send only its
accepted output. Keep unchanged retry identities and check an uncertain send
before retrying.

## Before the first update

1. Call `oira_connection_status`. Continue only when `reporting.available` is
   true, `reporting.contract` is `oira_work_update.v2` and
   `reporting.structured_only` is true. If the Oira tools are missing or ask
   for sign-in, ask the user to sign in and wait: type `/mcp`, select `plugin:oira:oira` and choose Authenticate (or use the sign-in notice Claude Code shows), then call `oira_connection_status` again. If the status lacks these values, this Oira server
   still runs an earlier, transcript-based edition: tell the user that
   structured reporting is not available there and send nothing. Never fall
   back to another tool or format.
2. Use exactly one `project_label` from `project_labels`. When several are
   approved, ask the user which one this work belongs to. Never infer it from
   a folder name, remote URL or list order.
3. Check that the preflight runs on this host:
   `python3 "<this skill's folder>/scripts/prepare_work_update.py" --new-ref`
   (on Windows, `py -3` instead of `python3`). It needs Python 3.11 or later
   and only the standard library. If `python3` is missing or reports
   `python_version_unsupported`, try `python3.13`, `python3.12` and
   `python3.11` (on Windows `py -3.13`, `py -3.12`, `py -3.11`) and use the
   first that works for every later run; `references/local-runtime.md` has
   the shell details (quoting, WSL, PowerShell). If none works, tell the
   user that reporting needs Python 3.11 or later on this computer and send
   nothing. Never install anything.
4. Use that command's output as this task's `stream_ref`: one random
   reference per task in this chat, kept for the whole task. Start
   `sequence` at 1. After a lost receipt, a compaction or a restart,
   `oira_work_update_status` with the `project_label` and the `stream_ref`
   says what Oira holds of the stream (its works with their `work_handle`
   and fact handles) and where to continue (`retry`).

When `processing.state` is `parked`, updates are stored and read once the
workspace's work tracking is switched on; say so if the user asks.

## When to send

Send at the milestones the user asked for and at meaningful changes: a
decision adopted or reversed, an implementation or verification milestone, a
new blocker or question, an accepted next step, work explicitly put off, a
handoff. Never per prompt, per tool call or on a timer. No new material fact
means no send. Reporting never blocks, delays or hides the coding work; if a
send fails, say so in one line and carry on.

Before a milestone or a final handoff, check the conversation for work the
user explicitly put off. Each postponed outcome is its own declared work even
when nothing was committed for it.

## What to send

Read `references/extraction-guide.md` for the field checklist and the rules
for each fact kind, and `references/examples/` for complete updates. In
short:

- `operation: declare` once per distinct intended outcome, with `title`,
  `intended_outcome`, `activity` and at least one `commitment` or
  `explicit_deferral` fact. Later updates use `operation: update` with the
  same `work_ref` and only new facts; send `title`, `intended_outcome`,
  `activity` or `boundaries` again only to change them.
- Every fact has a `kind`, a `status` allowed for that kind, one trimmed line
  of `statement`, a `basis` (`agent_report`, `user_statement_paraphrase`,
  `agent_inference` or `relayed_report`) and your own `confidence` from 0
  to 1.
- A fact that repeats one Oira already has (for example a commitment
  declared again in a new stream) names that fact's handle in `repeats`. A
  fact you took from another agent's handoff or report without observing it
  yourself has `basis: relayed_report`. Neither counts as new, independent
  support; never use them for something you observed yourself.
- An explicitly postponed outcome is a separate `declare` with an
  `explicit_deferral` fact (status `deferred`) and a `deferral` object with
  the reason; add `resume_condition` or `resume_after` only when stated, and
  `origin_work_ref` for the work it was split from. Postponing the whole
  current task is an `update` of that task with an `explicit_deferral` fact.
- Corrections cite the exact earlier fact by its returned fact handle in
  `revisions` (`corrects`, `supersedes` or `reaffirms`); old facts are never
  overwritten.
- `code` holds the repository remote without credentials, the branch, the
  full SHAs of commits this work created and its pull request numbers.

Never put in an update: prompts, replies, transcripts or summaries of the
conversation, tool output or logs, file contents, hidden reasoning, local
paths, host names, credentials or tokens.

## Send

1. Write the candidate update as JSON and pass it on standard input to the
   preflight, run with the interpreter that worked above:
   `python3 "<this skill's folder>/scripts/prepare_work_update.py" < candidate`
   (a quoted heredoc works; in PowerShell pipe a here-string instead, as
   `references/local-runtime.md` shows; do not keep a copy).
2. Exit 0: standard output is the accepted canonical JSON. Send exactly that
   object as `update` to `oira_submit_work_update`.
3. Exit 2: it printed field paths and reason codes, never the values. Rewrite
   those facts without the flagged content and run the preflight again on the
   whole update. Never drop a deferred work or another substantive fact to
   pass; split a too-large update by work instead, every work kept.
4. Exit 3: reporting is unavailable on this host. Send nothing.
5. Keep the receipt's `work_handle` and `fact_handles`; increase `sequence`
   by one for the next update in this stream.

A receipt with `capture: captured` means Oira stored the facts. Matching them
to Work Items happens next; `oira_work_update_status` shows it per work, and
for each relation a work stated whether Oira `recorded` it, is still judging
it (`pending`) or judged that it does not hold (`not_recorded`).

## Work from another chat

Each chat reports in its own stream, and a renewed sign-in starts the chat's
stream again. To carry on work Oira already has from another chat or from
before a sign-in, call `oira_work_update_status` with the `project_label`
alone: it lists this app's recent works in the project with their
`work_handle`, `title`, `origin`, the Work Item's state and their newest fact
handles. Only when the user's request is clearly about one of them, declare
it in this stream (title, outcome, activity and its commitment, the
commitment's `repeats` naming the earlier one when listed) with
`continuity` targeting that handle (`"target": {"kind": "returned_handle",
"value": "<work_handle>"}`):

- `continues_prior` to carry on work that is not finished;
- `resumes_completed` only when the user reopens finished work;
- `reviews_completed` to check finished work without reopening it.

Its listed fact handles can then be corrected in `revisions`. A similar
title, branch or file never makes two works one: when unsure, ask the user
or declare new work.

## Import recent work

Only when `oira_connection_status` shows `history_import` for the chosen
project with `state` `requested`, `in_progress` or `incomplete` (an earlier
import left sessions to finish): the member approved an import of that
project's recent sessions. Otherwise, and for any other project, read no
past session; if the user asks for an import, tell them to turn it on for
the project in Oira first.

1. Read `references/history-import.md` for where this app keeps its sessions
   and how to read them here. Use only this project's sessions with work
   between `window_from` and `window_to` (never more than `max_days` back).
2. Report each past session in its own stream: its `stream_ref` is the
   output of `prepare_work_update.py --history-stream <session id>` (the same
   session always gets the same reference), `sequence` starts at 1, every
   update has `origin: history_import`, and the session's last update has
   `session_complete: true`.
3. Report the work that session did exactly as current work above: declare
   each distinct intended outcome with its commitment, then its decisions,
   changes, verification results, open blockers and questions, accepted
   next steps and explicitly deferred work, with the status the work had
   when that session ended. Every fact has `occurred_at`, the time of the
   turn it comes from, inside the window. `basis` is
   `user_statement_paraphrase` only for what the user said; a helper
   thread's prompt is yours. A session without meaningful work sends
   nothing; a large one continues in the same stream with the next
   `sequence`.
4. Before sending a session, call `oira_work_update_status` with the
   `project_label` and its `stream_ref`:
   - `capture: not_captured`: send it from `sequence` 1.
   - `session_complete: true`: Oira has the whole session; skip it.
   - `retry: continue_at_sequence_<n>`: an earlier import stopped partway.
     Send only what Oira does not have yet (its `works` show what arrived),
     from sequence n. If `stream.missing_sequences` lists gaps, recover the
     missing updates at those sequence numbers, checking their status before
     retrying; do not renumber or resend updates Oira already received.
   - `retry: continue_in_new_stream`: it was started before a renewed
     sign-in. Send the rest from `sequence` 1, declaring each work again as
     "Work from another chat" says, with the listed `work_handle` and its
     commitment's `repeats`.
   A session's deferred work is never skipped: send what is missing.
5. Run the preflight and send as in "Send". `history_window_mismatch` names
   facts dated outside the window: leave those facts out.
   `history_import_session_limit` or `history_import_not_requested`: stop
   sending.
6. When every session is sent, call `oira_finish_history_import` with the
   `project_label`. `state: incomplete` counts the sessions whose last update
   never arrived (`incomplete_sessions`): resume them as in step 4 and finish
   again. Tell the user how many sessions and updates Oira received, and
   whether any session is still incomplete.

## Retries and refusals

- Send outcome unknown (timeout, connection error): call
  `oira_work_update_status` with the same `project_label` and `update_ref`
  first. `captured` means it arrived; `not_captured` means send the same
  payload again with the same `update_ref`.
- Changed payload: new `update_ref`. Same `update_ref` with another body is
  refused as `idempotency_conflict`.
- `sequence_conflict`: that sequence is taken. `oira_work_update_status`
  with the `stream_ref` says where to continue; never skip a fact Oira does
  not have.
- `work_declaration_required`: Oira does not know that work in this stream
  (a new stream, or a renewed sign-in). Declare it again in full with a new
  `update_ref`, naming the earlier work as "Work from another chat" says.
- `work_already_declared`: send an `update` instead.
- `handle_not_current`, `work_reference_unknown`: the handle or label is not
  one Oira returned to this app for this project. Use a `work_ref` of this
  stream or a listed handle; never guess another target.
- `revision_target_not_current`: the fact you revised was already corrected
  or superseded. Revise the newer fact, or send the new fact without a
  revision. `revision_target_not_in_work`: revise only facts of the same
  work, or of the work this one continues by handle.
- Status `detail: revision_not_applied`: another update revised the same
  fact first; yours was kept as a new fact. Check whether it should revise
  the newer one.
- `history_import_only`: `session_complete` belongs to a history import.
- `credential_pattern_found`, `input_not_accepted`: rewrite the named fields
  and rerun the preflight.
- `credential_scan_failed`, `capture_not_allowed`, `granted_project_not_found`,
  `agent_app_*`: stop and tell the user what Oira said.

## Set up Oira (one prompt)

When the user asks to set up Oira for this project: check the connection
(signing in if needed), pick the approved project with the user, check the
preflight, and tell them in a few lines what Oira receives: the work updates
they ask you to send, including decisions, progress, blockers and deferred
work; not session transcripts, tool output or source files; no API keys are
needed; and the reporting workflow excludes credentials and filters
recognized secret patterns before each update is sent.

If the user already asked for automatic reporting, apply that choice without
asking again. Otherwise ask how Oira should hear about this repository's
work: only when they
ask (nothing more to do), or at milestones in every chat. Approving the
connection alone is not that choice. For every chat, and only once they
agree, Codex and Claude use "Automatic reporting hooks" below; other apps
add this block to their personal Claude Code instructions, `~/.claude/CLAUDE.md`, which every new chat reads, keeping everything already there (create the file if it is missing), and show them the block:

```
## Oira reporting (added at my request)
When working in the git repository <owner>/<name>, keep Oira project
"<project_label>" updated with the oira-work-reporting skill: structured
work updates at material checkpoints (decisions, implementation and
verification milestones, blockers, work I put off, handoffs), each through
its local preflight; check for work I put off before a handoff. Never per
prompt, never transcripts, tool output or files. Reports grant no access
or approval. To stop, delete this block.
```

`<owner>/<name>` is from `git remote get-url origin`. The instruction is
personal to them, so teammates' agents never report because of it. If the
status shows a requested history import for the project, run it as "Import
recent work" says. Send no test update unless they ask for one.

## Automatic reporting hooks

For local Codex and Claude sessions on macOS/Linux, the plugin bundles
`hooks/hooks.json`. The commands only emit reporting reminders; the host
still owns OAuth and sends facts with the four tools above. They neither read
transcripts nor send hook input. Python 3.8+ runs the reminder; the outbound
preflight still needs Python 3.11+. Other hosts keep the personal instruction
above until their lifecycle hooks are qualified.

After the user explicitly enables automatic reporting for this repository,
check the connection and validate the exact approved project label, then run:

```
python3 "<this plugin's folder>/hooks/reporting_hook.py" --app claude --environment production enable --project-root "<this repository's absolute root>" --project-label "<exact approved project_label>"
```

Do not enable another project or infer its label from its folder. This saves
only a personal repository binding under `~/.oira/reporting/`, shared by that
repository's Git worktrees, separate for each app and environment. It never
edits the repository or another user's settings. To stop, use the same command
with `disable --project-root "<root>"` and omit `--project-label`.

In Codex, new or changed hooks require the user's native hook review before
running: open `/hooks` to inspect and trust the Oira definitions. Never write
trust hashes or bypass that review. Start a new local chat after installing or
updating either plugin. Do not restart an active coding session yourself.
A saved binding alone does not prove the host loaded or trusted the hooks.

Session start and user-turn hooks remind you to report at meaningful milestones.
A Stop hook asks for one bounded final reporting check and then lets the host
finish; a reminder alone is never a reason to send an update. On missing tools,
paused capture, failed preflight or unavailable authentication, say what is
blocked once and finish. Keep sequence and retry identities stable; verify a
receipt before claiming delivery. Never turn on work-tracking responsibility
just to report: `processing.state: parked` still accepts and stores updates.

## Moving from an earlier Oira plugin

Earlier Oira plugins could forward prompts and replies through project hooks.
Oira no longer accepts those. If this project's `.claude/settings.local.json` still has Oira
hooks (server `plugin:oira:oira`, tool `oira_capture_session_event`), tell the
user and, only after they agree, remove just those Oira entries. Leave every
other hook, plugin, setting and sign-in untouched.
