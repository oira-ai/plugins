# Past Copilot sessions and the Oira history import

The import of recent work is **not available for GitHub Copilot** in this
release. Oira does not request it for a Copilot connection, so
`oira_connection_status` never shows a `history_import` with state
`requested`, `in_progress` or `incomplete` for this app. Read no past
session.

If the user asks you to import earlier Copilot work, tell them in one line
that Copilot sessions cannot be imported yet, and offer the alternative
that works today: in a chat where the earlier work is still in context, or
in a new chat where they describe it, report it as current work ("Keep
Oira updated on this task" or "Share a progress update with Oira"), with
the facts they can confirm, the branch, and the commits and pull requests
`git log` shows. Never reconstruct a past session from the CLI's session
store under `~/.copilot`, an IDE's chat history, a resumed session's
transcript or any export: none of these is a qualified source of dated,
attributed work for Oira, and reading them is outside the member's
approval.

Why: Copilot keeps sessions in surface-specific stores whose layout is not
documented for this purpose, and the surfaces differ (CLI, VS Code,
JetBrains, Visual Studio). A qualified reader with session timestamps,
human versus agent attribution and helper-thread lineage is the
precondition for offering the import; until then this file stays the
instruction.
