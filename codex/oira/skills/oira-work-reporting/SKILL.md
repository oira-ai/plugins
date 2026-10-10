---
name: oira-work-reporting
description: Set up Oira for this project in one prompt (sign in, automatic project-local updates, recent history import), and send bounded progress updates, handoffs, corrections or connection tests to an approved Oira project.
---

# Oira work reporting

Use `oira_connection_status`, `oira_open_work_session`,
`oira_send_work_update`, and `oira_submission_status` for purposeful manual
reports, and `oira_import_history_session` with `oira_finish_history_import`
only for a requested history import. `oira_capture_session_event` is hook-only: never invoke it as an
ordinary model-selected reporting tool.

Always call `oira_connection_status` first. Work only with an exact approved
project label. A tool or hook cannot expand workspace, project, or content
access. Never infer the destination from a folder name, remote URL, the first
label, or the current organization.

## Set up Oira (one prompt)

When the user asks to set up, connect or install Oira for this project,
finish the whole setup in that one request, in this order. Stop only where
the user has to act, and continue when they say they are done.

1. **Sign in.** Call `oira_connection_status`. When the Oira tools are
   missing or ask for sign-in, tell the user to sign in and wait: Codex
   signs in when Oira is installed; if it did not, open Settings, then MCP
   servers, and choose Authenticate next to `oira`. In the browser, Oira
   opens with their workspace; they choose the projects this app may
   update, keep automatic updates and the history import on unless they do
   not want them, and approve. Then call `oira_connection_status` again.
2. **Pick the project.** When exactly one project label is approved, use it
   and name it. When several are, ask which one this folder belongs to;
   never guess from the folder name, remote URL or list order.
3. **Automatic updates.** When status shows automatic capture enabled with
   a binding for that label, ask before adding the hook, in a sentence or
   two: from now on each prompt the user types in this project and your
   final reply go to Oira exactly as typed, nothing else, so secrets do not
   belong in those prompts. Add it only after they say yes, as described in
   "Automatic forward updates": coding apps' safety reviews refuse the file
   change without that yes. When automatic capture is not enabled, skip
   this and say they can turn it on in Oira.
4. **Recent history.** When `history_import` shows `requested` for that
   label, import it now as described in "Import recent history", using the
   window Oira returns; do not ask for dates. Otherwise skip it.
5. **Confirm.** Tell the user in a few lines: the workspace and project, how
   many sessions and turns the import sent and, when you added the hook, what
   is left for them to turn it on in this app (see "Automatic forward
   updates"). Send no test report unless they ask for one.

## Manual reports

Open or resume one project stream. When the client exposes a stable native
session ID, pass it as `client_session_key` so a lost open response reuses the
same registration. Build `agent_work_report.v1` only from current context the
user intends to share. Keep absent facts absent; preserve unknown timing and
native lineage. Omit secrets, credentials, unrelated source, and unsupported
conclusions.

When the work is in a git repository, add `code` so Oira can tell when it
lands: `repository_url` (`git remote get-url origin`), `branch`
(`git branch --show-current`), the full SHAs of `commits` you created for this
work since your last report, and the numbers of `pull_requests` you opened for
it. Never list the commit you started from. Oira completes the Work Item once
that code reaches the default branch, whether it lands in one commit, several
pull requests, or a branch merge.

Use `checkpoint` for progress, `handoff` for continuation context,
`correction` with the prior receipt ID to amend a report, and
`test_connection` for a harmless connectivity test. Before consequential or
sensitive reports, summarize what will be sent. A receipt proves durable
capture only; use the separately reported processing state for interpretation.

If a send outcome is unknown, call `oira_submission_status` before retrying.
Retry the same submission identity only with an unchanged body. Use the newly
issued identity for changed content.

## Progress during long work

When the user enabled automatic updates for this project, or asked you to keep
Oira updated, also report progress while a long task is still underway. The
hooks send only the prompt and your final reply, so the decisions and
milestones in between are otherwise invisible until the turn ends, and a
teammate who depends on this work finds out late.

Send a `checkpoint` report through `oira_open_work_session` (with the same
`client_session_key` as this native session) and `oira_send_work_update`:

- after a material implementation decision or milestone: an approach chosen or
  reversed, a component finished, a blocker hit, a pull request opened;
- at the next point where you can act, if about an hour of active work has
  passed since your last progress report.

Include only facts that are new since your last report, from current context:
what changed, what was decided, what is blocked or next, and `code` with the
commits and pull requests you have. Never send tool arguments or output, file
contents, or a transcript, and do not repeat what an earlier report or the
hooks already sent. Mark each statement as your own summary
(`agent_conclusion`, or `paraphrase` when you restate the user): it is
derivative evidence, not an independent confirmation of what the hooks
captured. A pull request link or a progress report does not prove the change
was tested; say what was actually verified.

This is an opportunistic checkpoint, not a timer. If a tool call blocks or the
app is closed, nothing is sent, and Oira records that gap rather than guessing.
Use the same retry rule as any report: check an unknown outcome with
`oira_submission_status` before retrying.

## Import recent history

Oira can learn from the approved project's recent past. Do this only when
`oira_connection_status` shows `history_import.state` as `requested` for the
chosen project, or when the user asks you to import their recent history. It
is separate from automatic updates and has its own consent, which the member
gives when approving the project or with the Import button in Oira.

Follow `references/history-import.md` for where this app keeps its history.
Send only the user's prompts and your final replies from sessions in this
project's folder, inside the window Oira returns: never tool calls, tool
output, file contents or reasoning. Replace obvious secrets with
`[redacted]`. Send one session per `oira_import_history_session` call (split
long sessions into parts), skip sessions Oira already lists as received, then
call `oira_finish_history_import`. Tell the user how many sessions and turns
were sent.

The window is the member's: they chose the period when they asked for the
import, and their plan sets how far back it can reach
(`history_import_max_days` in status). Read no further back than
`window_from`; Oira refuses turns outside the window anyway. A helper thread
your session started is not a session of its own — send its turns with the
session that started it, marked with `helper`.

## Automatic forward updates

Configure automatic updates only after the user said yes to them knowing what
they send: tell them first and wait for the yes (a request to set up Oira is
not that yes; see step 3 above). Status must also say all of the following:

- automatic capture is available and enabled;
- the user chose an exact returned project label;
- that project has a current binding handle;
- the current host is Codex or Claude Code and supports the project-local
  configuration described in `references/automatic-capture.md`.

Make the exact project-local file change visible before applying it. Merge with
existing hooks; never overwrite unrelated configuration. Never place active
content hooks in the plugin-global `hooks/hooks.json`: a global hook may run
in unrelated projects before Oira can reject it. Do not copy a binding to
another repository, parent folder, worktree, member, or destination label.

Install only the Codex SessionStart, UserPromptSubmit, Stop, and Interrupt
entries in the reference for this exact project. The hooks send current lifecycle
metadata, user prompt text, and final assistant text. They never send cwd,
transcript paths, tool arguments, tool results, or Oira tool traffic. There is
no general secret scrubber: warn that secrets typed into an allowed prompt or
response are part of that explicitly enabled content category.

After writing the file, tell the user exactly how to turn the hooks on, since
Codex runs no new or changed hook until it is trusted. In the Codex app they
open Settings, then Hooks, and click Trust on each of the four Oira hooks
listed under this project (Reload hooks if they are missing); the Codex CLI
asks at its next start, where they choose Trust all and continue. The hooks
run from the next chat in this folder, so ask them to start one. You cannot
see that trust yourself: check Oira status after the next eligible event;
“awaiting project configuration and host trust” is not synced. Host startup
can precede MCP readiness, and hooks never block coding or force continuation.

Automatic mode is forward-only while the app, plugin, authorization, and MCP
connection are active. It does not wake a closed app, read historical
transcripts, backfill missed events, or keep an offline queue. A client without
a stable event ID has receive-time-only identity and weaker retry guarantees.
Missing activity remains an explicit coverage gap.

To pause automatic updates, use Oira settings first so the consent generation
changes, then remove only the Oira entries from the project-local file. Removing
a local hook does not revoke Oira OAuth; disconnecting Oira does not edit the
host file. Re-enabling an old manual-only grant requires a new consent flow.
