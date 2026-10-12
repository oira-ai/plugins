# Oira in GitHub Copilot: what to check and where things live

Read this during "Set up Oira" and whenever a Copilot-specific question
comes up (sign-in, a missing server, the personal instructions file,
removal). Oira is a remote MCP server; the package is this skill plus the
server's address. Nothing here changes the user's model, tool permissions,
organization policies or other servers. GitHub Copilot is independent of
Oira's GitHub repository connector: no GitHub App, token or repository
permission is involved.

## GitHub login versus Oira sign-in

Copilot's own login (`/login`, or the IDE's GitHub account) is not an Oira
sign-in. Oira has its own OAuth: in the Copilot CLI, `/mcp auth oira`
opens the browser (or open `/mcp`, select `oira` and choose its auth
action); `/mcp show oira` lists the server with its four tools afterwards.
In VS Code, JetBrains and Visual Studio, the MCP server list (Configure
Tools, or the tools icon in chat) has a Start or Authenticate action next
to `oira`. When the sign-in used the wrong Oira account, sign in again from
the same surface and ask the user to disconnect the old connection in Oira.

A disabled server, an organization MCP policy or allowlist, a workspace
that is not trusted, or MCP autostart turned off can hide the server: say
which control applies and stop. Never ask the user to disable such a
control, to approve every tool, or to lower workspace trust.

## Where the pieces are

| Piece | Location |
| --- | --- |
| Plugin (CLI and VS Code) | installed by `copilot plugin install oira@oira` into `~/.copilot/installed-plugins/oira/oira/` (or `_direct/...` for a direct source); VS Code lists it under Agent Plugins → Installed |
| Skill by hand | `~/.copilot/skills/oira-work-reporting/` (CLI, VS Code, Visual Studio 2026 18.5+; `%USERPROFILE%\.copilot\skills\...` on Windows) or `.github/skills/oira-work-reporting/` in one project |
| MCP server by hand | CLI: `~/.copilot/mcp-config.json` (`$COPILOT_HOME/mcp-config.json` when set), `mcpServers` form with `type: http` and the four tool names in `tools`; VS Code: `.vscode/mcp.json` (`servers` form) or portable `.mcp.json` (`mcpServers` form); JetBrains and Visual Studio: their MCP editor (`servers` form, `url` only) |
| Personal reporting instruction | `~/.copilot/copilot-instructions.md` (`$COPILOT_HOME/copilot-instructions.md` when set) |

Skill folders need `SKILL.md`, `references/` and `scripts/`: if
`scripts/prepare_work_update.py` is missing, the copy was incomplete and
reporting is unavailable until the folder is complete. Reporting needs
Python 3.11 or later on this computer and nothing else: no Node (Copilot's
npm install needs it, the reporting does not), no SDK, no extension.

Project files (`.mcp.json`, `.github/mcp.json`) override the personal
file for servers with the same name, and `.vscode/mcp.json` is read by VS
Code only, not by the CLI. When the tools are missing, check which file
defines `oira` for the surface in use (`/mcp show oira` names the source).

## The personal reporting instruction

When the user chooses reporting in every chat, the block from SKILL.md goes
into `~/.copilot/copilot-instructions.md` (create it if missing; keep
anything already there). The Copilot CLI and Agent Host sessions read it in
every chat; `/instructions` in the CLI lists the instruction files found,
which is how to confirm it. A VS Code local session, JetBrains or Visual
Studio may not read that file: tell the user to check, and that until then
the per-task request ("Keep Oira updated on this task") is the way to
report. Never write the block into a repository file
(`.github/copilot-instructions.md`, `AGENTS.md`) or into another agent's
file: those would opt in everyone who opens the repository.

## Removal

To stop reporting from this computer: remove the Oira block from
`~/.copilot/copilot-instructions.md` (delete the file only when nothing
else is in it); `copilot plugin uninstall oira` or VS Code's Uninstall in
Agent Plugins, whichever installed it; for a hand installation delete the
skill folder and the `oira` entry from the MCP configuration file that
holds it. Ask the user to disconnect the connection in Oira as well: a
local sign-out or a deleted entry does not revoke the grant Oira holds.
Leave every other skill, server, instruction file, plugin and policy
untouched; a differently named Oira package on the same computer (its own
server key and skill folder) is not part of this removal.
