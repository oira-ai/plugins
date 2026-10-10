# Importing recent Claude Code history into Oira

Run this only when `oira_connection_status` shows `history_import.state` as
`requested` for the chosen project, or when the user asks you to import their
recent history. Import only that approved project, only inside the window Oira
returns, and only the user's prompts and your final replies.

## Where Claude Code keeps history

One file per session under `~/.claude/projects/`, in a folder named after the
project path with every `/` replaced by `-` (for example
`/Users/ana/web-app` becomes `-Users-ana-web-app`):
`<session id>.jsonl`. Each line is one JSON record with `timestamp`,
`sessionId`, `cwd` and `gitBranch`. Subagents the session started keep their
own files under `<session id>/subagents/`, in nested folders too; their work
belongs to the session that started them (see "Helper threads").

- A user prompt is a record with `"type": "user"` that is not `isMeta`,
  `isSidechain` or `isCompactSummary` (the "This session is being continued"
  summary). When its `message.content` is a list, skip it if any block is a
  `tool_result`; otherwise keep its `text` blocks and drop images.
- When the record has `origin`, keep it only if `origin.kind` is `human`:
  `task-notification` is a background task reporting back and `peer` is
  another Claude session. Older versions write no `origin`.
- Remove `<system-reminder>…</system-reminder>` blocks, then skip text that is
  empty or starts with `<task-notification>`, `<local-command-`, `<bash-` or
  `[Request interrupted by user`: the app wrote those, not the user.
- A slash command is text with `<command-name>/x</command-name>` and
  `<command-args>`: send it as `/x args`. Skip one that gets no reply; local
  commands such as `/model` never do.
- A prompt typed while you were mid-turn is not a user record. It is a
  `"type": "attachment"` record whose `attachment.type` is `queued_command`
  and `attachment.commandMode` is `prompt`, with the words in
  `attachment.prompt` (a string or blocks, read as above). Add it to the
  current turn's prompt, unless `attachment.isMeta` is true or
  `attachment.origin.kind` is `peer`: those come from other Claude sessions.
- Your replies are records with `"type": "assistant"`; `message.content` is a
  list of blocks. Skip records with `isApiErrorMessage` or whose
  `message.model` is `<synthetic>`. The final reply of a turn is the `text` of
  the last `text` block before the next user prompt.

## What to send

Use only sessions from this project's folder, and only turns whose
`occurred_at` is on or after `window_from` and before `window_to`. The window
is what the member asked for, within what their plan covers:
`oira_connection_status` also reports `history_import_max_days`, and Oira
refuses a turn outside the window it gave you. For each
session call `oira_import_history_session` with:

- `project_label`: the approved project label;
- `app_session_key`: the `sessionId`;
- `git`: `branch` from `gitBranch` and `repository_url` from
  `git -C <project folder> remote get-url origin` when it succeeds, plus the
  `commits` and `pull_requests` the session created inside the window (see
  below). Leave `commit` out: today's `HEAD` is not where the session started;
- `turns`: one entry per turn with `occurred_at` (the final reply's
  `timestamp`, or the prompt's when the turn has none), `prompt` (the user's
  words) and `final_reply`.

## Helper threads

A subagent's work is part of the session that started it, so send its turns
with that session, marked, instead of as a session of their own. For each
file under `<session id>/subagents/` (including nested ones) whose session
you are sending:

- read its turns exactly as above — a subagent's prompt is a `"type": "user"`
  record with `isSidechain` true, which you skip for the user's own turns;
- add each one to the parent session's `turns` with `helper` set to a short
  name for the subagent (its folder or agent name, e.g. `reviewer`);
- keep them in time order with the parent's own turns.

Oira reads a `helper` turn as the coding agent talking to itself: the prompt
is your request, not the user's. Leave `helper` out for the user's own turns.

Never send tool calls, tool output, file contents, thinking, or anything
outside the window. Replace obvious secrets (API keys, tokens, passwords) with
`[redacted]`, but never a whole prompt or reply, and truncate a `prompt` or
`final_reply` to 8,000 characters. Send at most 40 turns and about 1 MB per
call; split a longer session into parts with `part` and `last_part`, and if
Oira refuses a call as too large, send its turns in smaller parts. Skip
sessions Oira already lists as received. Oira identifies a session part by its
turns alone: sending the same turns again returns `replayed` and ignores any
changed `git`, so get `git` right before the first send. When every session
is sent, call `oira_finish_history_import`.

## Finding commits and pull requests

Look at the tool calls the session and its subagents made inside the window.
Read tool results only to find these identifiers; never send them.

- `commits`: take the SHA from every `[<branch> <sha>]` line and every SHA
  that starts a line in any tool result, whichever command printed it: a
  session can commit through its own script, and after `git commit -q` only a
  following `git log --oneline` prints the SHA. Resolve each with
  `git -C <project folder> show -s --format='%H %cI' <sha>`. Keep the full SHA
  only if it was committed while that same call ran (from one second before
  the `timestamp` of the record holding the `tool_use` to one second after
  that of the record holding its `tool_result`; `%cI` has whole seconds) and
  `git -C <project folder> for-each-ref --contains <sha>` prints a ref (an
  amended-away commit prints none). A `git log` of earlier commits fails the
  time check by itself. If more than one session keeps the same SHA, only
  the session whose call was shortest keeps it.
- `pull_requests`: the numbers of pull requests opened (the `/pull/<number>`
  URL `gh pr create` printed).

Read the files with whatever you already have: a short throwaway script, `jq`,
or reading them directly. Nothing needs to be installed.
