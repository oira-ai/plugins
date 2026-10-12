# Reading recent Codex sessions for an Oira history import

Use this only during a history import the member approved (see "Import
recent work" in SKILL.md). You read the sessions here, on this computer, to
understand what work was done. Oira receives only the structured work
updates you write about them: never a session file, prompt, reply, tool
output or file content.

## Where Codex keeps sessions

One file per session under `$CODEX_HOME/sessions` (by default
`~/.codex/sessions`), in dated folders:
`YYYY/MM/DD/rollout-<timestamp>-<id>.jsonl`. Each line is one JSON record.

- The first record has `"type": "session_meta"`. Its `payload.cwd` is the
  folder the session ran in, `payload.id` is the session id, and
  `payload.git` holds `repository_url`, `branch` and `commit_hash`.
- Helper agents and approval reviews that a session starts get files of
  their own in the same folders. Their `session_meta` has
  `payload.parent_thread_id` (the thread that started them) and a
  `payload.source` with `subagent`. They are not sessions of their own (see
  "Helper threads").

Use only sessions without `payload.parent_thread_id` whose `cwd` is this
project's folder or inside it, with turns inside the window.

## What the user said and what you replied

- A turn starts with an `event_msg` record whose `payload.type` is
  `task_started` and ends with one whose `payload.type` is `task_complete`.
  That record's `payload.last_agent_message` is the final reply and its
  `timestamp` is when the turn ended: the `occurred_at` of facts from that
  turn.
- The user's words are in `response_item` records with
  `payload.type: "message"` and `payload.role: "user"`, including messages
  typed while the turn ran. Ignore items whose text starts with `<` (for
  example `<environment_context>`) or with `# AGENTS.md instructions`: Codex
  injects those; the user did not write them.

## Helper threads

A helper's prompt was written by Codex, not by the user, and its work is
part of the session that started it. For a file whose
`payload.parent_thread_id` leads back to a session you are importing, read
only its own records (those at or after
`payload.subagent_history_start_ordinal`; the ones before are a copy of the
parent's history) to learn what that session did. Report that work in the
parent session's stream, and never attribute a helper's prompt to the user.

## Finding commits and pull requests

Look at the tool calls made inside the window by the session and by the
helper agents whose `parent_thread_id` leads back to it. Read tool output
only to find these identifiers.

- Commits: take the SHA from every `[<branch> <sha>]` line and every SHA that
  starts a line in any tool output, whichever command printed it. Resolve
  each with `git -C <project folder> show -s --format='%H %cI' <sha>`. Keep
  the full SHA only if it was committed while that same call ran (from one
  second before the call record's `timestamp` to one second after that of
  the output record with the same `payload.call_id`) and
  `git -C <project folder> for-each-ref --contains <sha>` prints a ref (an
  amended-away commit prints none). If more than one session keeps the same
  SHA, only the session whose call was shortest keeps it.
- Pull requests: the numbers of pull requests opened (the `/pull/<number>`
  URL `gh pr create` printed).
- The repository and branch come from `payload.git`; send the repository
  without any credentials.

Read the files with what you already have: a short throwaway script, `jq`,
or reading them directly. Nothing needs to be installed, and nothing you
read is kept or sent.
