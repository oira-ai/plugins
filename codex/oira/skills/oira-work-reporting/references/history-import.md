# Importing recent Codex history into Oira

Run this only when `oira_connection_status` shows `history_import.state` as
`requested` for the chosen project, or when the user asks you to import their
recent history. Import only that approved project, only inside the window Oira
returns, and only the user's prompts and your final replies.

## Where Codex keeps history

One file per session under `$CODEX_HOME/sessions` (by default
`~/.codex/sessions`), in dated folders:
`YYYY/MM/DD/rollout-<timestamp>-<id>.jsonl`. Each line is one JSON record.

- The first record has `"type": "session_meta"`. Its `payload.cwd` is the
  folder the session ran in, `payload.id` is the session id, and
  `payload.git` holds `repository_url`, `branch` and `commit_hash`.
- Helper agents and approval reviews that a session starts get files of their
  own in the same folders. Their `session_meta` has `payload.parent_thread_id`
  (the thread that started them) and a `payload.source` with `subagent`. They
  are not sessions of their own: Codex wrote their prompts, and their work
  belongs to the session that started them (see "Helper threads").
- A turn starts with an `event_msg` record whose `payload.type` is
  `task_started` and ends with one whose `payload.type` is `task_complete`.
  That record's `payload.last_agent_message` is the final reply and its
  `timestamp` is when the turn ended.
- The user's words are in `response_item` records with
  `payload.type: "message"` and `payload.role: "user"`: join the `text` of
  their `content` items, including messages typed while the turn ran. Skip
  items whose text starts with `<` (for example `<environment_context>` or
  `<recommended_plugins>`) or with `# AGENTS.md instructions`. Codex injects
  those; the user did not write them.

## What to send

Use only sessions without `payload.parent_thread_id` whose `cwd` is this
project's folder or inside it, and only turns whose end time is on or after
`window_from` and before `window_to`. The window is what the member asked
for, within what their plan covers: `oira_connection_status` also reports
`history_import_max_days`, and Oira refuses a turn outside the window it
gave you. For each session call
`oira_import_history_session` with:

- `project_label`: the approved project label;
- `app_session_key`: the session's `payload.id`;
- `git`: `repository_url`, `branch` and `commit` (where the session started)
  from `payload.git`, when present, plus the `commits` and `pull_requests`
  the session created inside the window (see below);
- `turns`: one entry per completed turn with `occurred_at` (the
  `task_complete` timestamp), `prompt` (the user's words) and `final_reply`
  (`last_agent_message`).

## Helper threads

A helper's work is part of its parent session, so send its turns with that
session, marked, instead of as a session of their own. For each file whose
`payload.parent_thread_id` leads back to a session you are sending:

- its own records are the ones at or after `payload.subagent_history_start_ordinal`
  (Codex copies the parent's history before that point — never send the copy);
- from those records read turns exactly as above, and add each one to the
  parent session's `turns` with `helper` set to a short name for the helper
  (`payload.source.subagent` and its label, e.g. `reviewer`);
- keep them in time order with the parent's own turns.

Oira reads a `helper` turn as the coding agent talking to itself: the prompt
is your request, not the user's. Leave `helper` out for the user's own turns.

Never send tool calls, tool output, file contents, reasoning, or anything
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

Look at the tool calls made inside the window by the session and by the
helper agents whose `parent_thread_id` leads back to it. Read tool output only
to find these identifiers; never send it.

- `commits`: take the SHA from every `[<branch> <sha>]` line and every SHA
  that starts a line in any tool output, whichever command printed it: a
  session can commit through its own script, and after `git commit -q` only a
  following `git log --oneline` prints the SHA. Resolve each with
  `git -C <project folder> show -s --format='%H %cI' <sha>`. Keep the full SHA
  only if it was committed while that same call ran (from one second before
  the call record's `timestamp` to one second after that of the output record
  with the same `payload.call_id`; `%cI` has whole seconds) and
  `git -C <project folder> for-each-ref --contains <sha>` prints a ref (an
  amended-away commit prints none). A `git log` of earlier commits fails the
  time check by itself. If more than one session keeps the same SHA, only
  the session whose call was shortest keeps it.
- `pull_requests`: the numbers of pull requests opened (the `/pull/<number>`
  URL `gh pr create` printed).

Read the files with whatever you already have: a short throwaway script, `jq`,
or reading them directly. Nothing needs to be installed.
