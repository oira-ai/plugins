# Past Cursor sessions and the Oira history import

The import of recent work is **not available for Cursor** in this release.
Oira does not request it for a Cursor connection, so
`oira_connection_status` never shows a `history_import` with state
`requested`, `in_progress` or `incomplete` for this app. Read no past
session.

If the user asks you to import earlier Cursor work, tell them in one line
that Cursor sessions cannot be imported yet, and offer the alternative that
works today: in a chat where the earlier work is still in context, or in a
new chat where they describe it, report it as current work ("Keep Oira
updated on this task" or "Share a progress update with Oira"), with the
facts they can confirm, the branch, and the commits and pull requests
`git log` shows. Never reconstruct a past session from the editor's
`state.vscdb` or workspace storage, the `~/.cursor` chat stores, the CLI's
histories, a cloud conversation export or team analytics: none of these is
a qualified source of dated, attributed work for Oira, and reading them is
outside the member's approval.

Why: Cursor keeps conversations in editor and CLI stores whose layout is
not documented for this purpose. A qualified reader with session
timestamps, human versus agent attribution and helper-thread lineage is
the precondition for offering the import; until then this file stays the
instruction.
