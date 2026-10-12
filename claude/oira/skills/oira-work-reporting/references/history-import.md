# Reading recent Claude Code sessions for an Oira history import

Use this only during a history import the member approved (see "Import
recent work" in SKILL.md). You read the sessions here, on this computer, to
understand what work was done. Oira receives only the structured work
updates you write about them: never a session file, prompt, reply, tool
output or file content.

## Where Claude Code keeps sessions

One file per session under `~/.claude/projects/`, in a folder named after the
project path with every `/` replaced by `-` (for example `/Users/ana/web-app`
becomes `-Users-ana-web-app`): `<session id>.jsonl`. Each line is one JSON
record with `timestamp`, `sessionId`, `cwd` and `gitBranch`. Subagents the
session started keep their own files under `<session id>/subagents/`, in
nested folders too; their work belongs to the session that started them
(see "Helper threads").

Use only sessions in this project's folder with turns inside the window.

## What the user said and what you replied

- A user prompt is a record with `"type": "user"` that is not `isMeta`,
  `isSidechain` or `isCompactSummary` (the "This session is being continued"
  summary). When its `message.content` is a list, skip it if any block is a
  `tool_result`; otherwise read its `text` blocks.
- When the record has `origin`, it is the user's only if `origin.kind` is
  `human`: `task-notification` is a background task reporting back and
  `peer` is another Claude session. Older versions write no `origin`.
- Ignore `<system-reminder>…</system-reminder>` blocks and text that starts
  with `<task-notification>`, `<local-command-`, `<bash-` or
  `[Request interrupted by user`: the app wrote those, not the user.
- A prompt typed while you were mid-turn is a `"type": "attachment"` record
  whose `attachment.type` is `queued_command` and `attachment.commandMode` is
  `prompt`, with the words in `attachment.prompt`; it is the user's unless
  `attachment.isMeta` is true or `attachment.origin.kind` is `peer`.
- Your replies are records with `"type": "assistant"`; `message.content` is a
  list of blocks. Skip records with `isApiErrorMessage` or whose
  `message.model` is `<synthetic>`. The final reply of a turn is the `text` of
  the last `text` block before the next user prompt.
- A fact's `occurred_at` is the `timestamp` of the turn it comes from: the
  final reply's, or the prompt's when the turn has none.

## Helper threads

A subagent's prompt was written by you, not by the user, and its work is part
of the session that started it. Read its files (a subagent's prompt is a
`"type": "user"` record with `isSidechain` true) only to learn what that
session did, report that work in the parent session's stream, and never
attribute a subagent's prompt to the user.

## Finding commits and pull requests

Look at the tool calls the session and its subagents made inside the window.
Read tool results only to find these identifiers.

- Commits: take the SHA from every `[<branch> <sha>]` line and every SHA that
  starts a line in any tool result, whichever command printed it. Resolve
  each with `git -C <project folder> show -s --format='%H %cI' <sha>`. Keep
  the full SHA only if it was committed while that same call ran (from one
  second before the `timestamp` of the record holding the `tool_use` to one
  second after that of the record holding its `tool_result`) and
  `git -C <project folder> for-each-ref --contains <sha>` prints a ref (an
  amended-away commit prints none). If more than one session keeps the same
  SHA, only the session whose call was shortest keeps it.
- Pull requests: the numbers of pull requests opened (the `/pull/<number>`
  URL `gh pr create` printed).
- The repository is `git -C <project folder> remote get-url origin`, sent
  without any credentials; the branch is the session's `gitBranch`.

Read the files with what you already have: a short throwaway script, `jq`,
or reading them directly. Nothing needs to be installed, and nothing you
read is kept or sent.
