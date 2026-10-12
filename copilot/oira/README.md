# Oira for GitHub Copilot

Keep [Oira](https://oira-oira.com) updated on your coding work from GitHub
Copilot (the Copilot CLI, VS Code, JetBrains IDEs or Visual Studio): when
you ask, the agent sends structured work updates (decisions, progress,
verification, blockers, questions, next steps and the work you explicitly
put off) for the project you approve. It never sends prompts, replies,
transcripts, tool output or files, and it needs no API key. Oira is a remote
MCP server; this package is the Oira skill plus its address.

This is the Copilot package, version **0.8.0**, in the Agent Plugins 1.0
layout: `plugin.json`, `mcp.json` (the remote server) and
`skills/oira-work-reporting/` (`SKILL.md`, `references/` including
`setup-and-sign-in.md` and `client-surfaces.md`, and
`scripts/prepare_work_update.py`, the local preflight that runs before
every update; Python 3.11 or later, standard library only, no network).
The same skill, preflight and contract are used by the Claude Code, Codex,
Kiro and Cursor packages. It is independent of Oira's GitHub repository
connector: no GitHub App, token or repository permission is involved.

Requirements: a current Copilot CLI (Windows needs PowerShell 6 or later;
the npm install needs Node 22 or later, the reporting itself needs no
Node), or VS Code with Copilot, or the Copilot plugin for a JetBrains IDE
2025.2 or later, or Visual Studio 2026 18.5 or later; and Python 3.11 or
later on the computer where the agent runs. No Copilot surface is verified
on a real host yet: the [setup guide](https://oira-oira.com/coding-agent-help)
shows the state of each surface per operating system. The GitHub cloud
coding agent, GitHub.com chat, code review, completions and headless runs
are not supported.

## Install

### Copilot CLI (also makes the plugin visible in VS Code)

In the CLI or any terminal:

    copilot plugin marketplace add oira-ai/plugins
    copilot plugin install oira@oira
    copilot plugin list

The listing must show `oira` from the `oira` marketplace. VS Code discovers
plugins installed by the CLI (Agent Plugins → Installed), so one install
serves both. Installing straight from the repository folder also works:
`copilot plugin install oira-ai/plugins:copilot/oira`. To update later:
`copilot plugin marketplace update oira` then `copilot plugin update oira`.

### VS Code without the CLI

Run **Chat: Install Plugin From Source** and enter
`https://github.com/oira-ai/plugins.git`; if VS Code asks which plugin of
the repository to install, choose the one at `copilot/oira` (never
`claude/oira`). Alternatively download the repository and point the
`chat.pluginLocations` setting at its `copilot/oira` folder, or add the
marketplace in the Agent Customizations editor. Check that Oira appears
under Agent Plugins → Installed and that its MCP server `oira` is listed
under Configure Tools. The `/plugin` commands and the Customizations
editor keep separate inventories: update and remove Oira from the one you
installed it with.

### By hand (JetBrains, Visual Studio, older builds, or no plugin loader)

1. Copy the whole `skills/oira-work-reporting` folder (with `references`
   and `scripts`) into your personal skills folder:
   `~/.copilot/skills/oira-work-reporting/` on macOS and Linux,
   `%USERPROFILE%\.copilot\skills\oira-work-reporting\` on Windows (or
   `.github/skills/oira-work-reporting/` inside one project). Visual Studio
   2026 18.5+ reads the same personal folder.
2. Add the Oira server where your surface reads MCP servers:
   - Copilot CLI: merge into `~/.copilot/mcp-config.json` (or
     `$COPILOT_HOME/mcp-config.json`), keeping every other server:

         {
           "mcpServers": {
             "oira": {
               "type": "http",
               "url": "https://oira-oira.com/mcp",
               "tools": [
                 "oira_connection_status",
                 "oira_submit_work_update",
                 "oira_work_update_status",
                 "oira_finish_history_import"
               ]
             }
           }
         }

     (`copilot mcp add --transport http --tools "oira_connection_status,oira_submit_work_update,oira_work_update_status,oira_finish_history_import" oira https://oira-oira.com/mcp`
     writes the same entry; `tools` is required for remote servers, and
     without `--tools` the CLI would allow every tool.) A portable project
     `.mcp.json` takes the same `mcpServers` entry.
   - VS Code: **MCP: Add Server**, or `.vscode/mcp.json` with
     `{"servers": {"oira": {"type": "http", "url": "https://oira-oira.com/mcp"}}}`,
     or a portable `.mcp.json` with the `mcpServers` form above.
   - JetBrains Copilot plugin: Copilot chat → tools icon → **Configure your
     MCP server**, and merge `{"servers": {"oira": {"url": "https://oira-oira.com/mcp"}}}`.
     Do not add a token header; Oira signs in with OAuth.
   - JetBrains AI Assistant (Copilot as its agent): Settings → Tools → AI
     Assistant → Model Context Protocol (MCP), add a server and merge
     `{"mcpServers": {"oira": {"url": "https://oira-oira.com/mcp"}}}`; then
     enable **Pass custom MCP servers** under Settings → Tools → AI
     Assistant → Agents, or the Copilot agent never sees it. Local projects
     only.
   - Visual Studio: tools icon → add a remote server with the URL
     `https://oira-oira.com/mcp`.

Never add headers, credentials, a client id or extra scopes: Oira uses
dynamic client registration with PKCE and the scopes it advertises.

## Sign in and set up

Start a new chat in your project. In the CLI, run `/mcp auth oira` and
finish in the browser (`/mcp show oira` lists its four tools). In an IDE,
use the Start or Authenticate action next to `oira` in the MCP server
list. Your GitHub login is not an Oira sign-in. Then send:

> Set up Oira for this project.

The agent picks the approved project with you, checks its local preflight,
tells you what Oira receives, and asks whether Oira should hear about this
repository only when you ask or at milestones in every chat. Only for the
second, and only after you agree, it adds a short instruction to your
personal Copilot instructions file `~/.copilot/copilot-instructions.md`
(nothing is written to the repository, so teammates are never opted in);
`/instructions` shows whether your surface loads that file.

Then ask it to "Keep Oira updated on this task", "Share a progress update
for this project with Oira" or "Prepare and share a handoff for this project
with Oira". Updates are sent only when you ask, at milestones and
meaningful changes, never per prompt or in the background.

The import of recent work is **not available for Copilot** in this version.
Current work is reported when you ask.

## If something is off

- The Oira tools are missing: `/mcp show oira` (CLI) or the MCP server list
  (IDE) must show the server and its four tools; a disabled server, a
  policy or allowlist of your organization, or workspace trust can hide
  it. Enable it or ask your administrator; Oira never asks you to disable
  those controls.
- Sign-in keeps repeating or used the wrong Oira account: `/mcp auth oira`
  again (CLI) or re-authenticate the server (IDE), and disconnect the old
  connection in Oira.
- "Reporting is unavailable": the preflight needs Python 3.11 or later;
  `references/local-runtime.md` in the skill explains the shell details.
- Both the plugin and a hand-copied skill are installed: keep one; the
  agent shows the duplicate and removes only the Oira copy you choose.
- More in the [setup and troubleshooting guide](https://oira-oira.com/coding-agent-help).

## Remove

`copilot plugin uninstall oira` (or uninstall from VS Code's Agent Plugins
view, whichever installed it); for a hand installation delete the skill
folder and the `oira` entry from the MCP configuration you edited; remove
the Oira block from `~/.copilot/copilot-instructions.md`; and disconnect
the connection in Oira (a local sign-out does not revoke it). Everything
else in your Copilot configuration stays as it was.

## What Oira receives

Oira receives only work updates you authorize, including decisions,
progress, blockers and deferred work. It does not collect your session
transcripts, tool output or source files, and you do not need to provide
API keys. The reporting workflow excludes credentials and filters recognized
secret patterns before sending an update; pattern checks cannot prove that
free text never contains a secret, so keep secrets out of what you ask your
agent to report. Read the [privacy policy](https://oira-oira.com/privacy)
and the [terms](https://oira-oira.com/terms). Support: nikita@oira-oira.com.
