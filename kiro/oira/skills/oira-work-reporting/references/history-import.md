# Past Kiro sessions and the Oira history import

The import of recent work is **not available for Kiro** in this release.
Oira does not request it for a Kiro connection, so `oira_connection_status`
never shows a `history_import` with state `requested`, `in_progress` or
`incomplete` for this app. Read no past session.

If the user asks you to import earlier Kiro work, tell them in one line that
Kiro sessions cannot be imported yet, and offer the alternative that works
today: in a chat where the earlier work is still in context, or in a new
chat where they describe it, report it as current work ("Keep Oira updated
on this task" or "Share a progress update with Oira"), with the facts they
can confirm, the branch, and the commits and pull requests `git log` shows.
Never reconstruct a past session from Kiro's local session store, a
`/chat save` export or the session dashboard: none of these is a qualified
source of dated, attributed work for Oira, and reading them is outside the
member's approval.

Why: Kiro keeps sessions in a local database under `~/.kiro/` whose layout
is not documented for this purpose, `/chat save` exports have no documented
schema, and cloud sessions cannot be exported locally. A qualified reader
for a representative CLI and IDE export, with session timestamps, human
versus agent attribution and helper-thread lineage, is the precondition for
offering the import; until then this file stays the instruction.
