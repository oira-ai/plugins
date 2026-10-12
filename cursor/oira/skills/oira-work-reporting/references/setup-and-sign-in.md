# Oira in Cursor: what to check and where things live

Read this during "Set up Oira" and whenever a Cursor-specific question
comes up (sign-in, a missing server, the personal User Rules, removal).
Oira is a remote MCP server; the package is this skill plus the server's
address. Nothing here changes the user's model, mode, permissions, team
controls or other servers.

## Cursor login versus Oira sign-in

Cursor's own account (`agent login`, `CURSOR_API_KEY`, the editor sign-in)
is not an Oira sign-in. Oira has its own OAuth: in the editor, Cursor
Settings → MCP (or Customize → MCP) shows `oira` with a login or
authenticate action that opens the browser; in the CLI, `agent mcp login
oira` does the same and `agent mcp list-tools oira` lists its four tools
afterwards. When the sign-in used the wrong Oira account, sign in again
from the same surface and ask the user to disconnect the old connection in
Oira.

A disabled server (enable it in the MCP list or with `agent mcp enable
oira`), a team allowlist or MCP configuration policy, or a project
`.cursor/mcp.json` entry that overrides the personal one can hide the
server: say which applies and stop. Never recommend `--approve-mcps`, a
blanket auto-run setting, or loosening team controls.

## Where the pieces are

| Piece | Location |
| --- | --- |
| Local plugin (editor) | `~/.cursor/plugins/local/oira/` (`%USERPROFILE%\.cursor\plugins\local\oira\` on Windows): `plugin.json`, `mcp.json`, `skills/oira-work-reporting/` |
| Skill by hand | `~/.cursor/skills/oira-work-reporting/` (or `.cursor/skills/oira-work-reporting/` in one project) |
| MCP server by hand | `~/.cursor/mcp.json` (personal) or `.cursor/mcp.json` (project), `mcpServers` form with `url` only |
| Personal reporting instruction | Cursor Settings → Rules → User Rules (a setting, not a file) |

Skill folders need `SKILL.md`, `references/` and `scripts/`: if
`scripts/prepare_work_update.py` is missing, the copy or plugin was
incomplete and reporting is unavailable until the folder is complete.
Reporting needs Python 3.11 or later on this computer and nothing else.

Cursor also reads skills from `.agents/skills`, `.claude/skills`,
`.codex/skills` and their personal equivalents. If an Oira skill for
another app appears beside this one, use the Cursor installation and tell
the user; never delete the other app's installation. One Oira installation
per computer for Cursor: not the plugin and a hand-copied skill together.

Use Agent mode. Ask and read-only modes cannot run the preflight or call
the submit tool; say so instead of switching the mode yourself.

## The personal reporting instruction

When the user chooses reporting in every chat, show them the block from
SKILL.md to paste into their personal User Rules (Cursor Settings → Rules
→ User Rules). Those rules are a setting, not a file: write nothing
yourself, and confirm with them that it was added. User Rules are
documented for the editor's Agent chats; whether the Cursor CLI or Cursor
inside a JetBrains IDE loads them is not verified, so on those surfaces
keep reporting per task until it is. Never put the block
into `.cursor/rules/` or another project file: that would opt in everyone
who opens the repository. Personal skills and rules are not sent to Cloud
Agents unless the user turned that sync on; Oira is not qualified there.

## Removal

To stop reporting from this computer: ask the user to remove the Oira
block from their User Rules; delete `~/.cursor/plugins/local/oira` (plugin
route) or the skill folder and the `oira` entry from the `mcp.json` that
holds it (manual route). Ask the user to disconnect the connection in Oira
as well: a local sign-out or a deleted entry does not revoke the grant
Oira holds. Leave every other skill, server, rule, plugin and policy
untouched; a differently named Oira package on the same computer (its own
server key and skill folder) is not part of this removal.
