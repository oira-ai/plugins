# Oira for Cursor

Keep [Oira](https://oira-oira.com) updated on your coding work from Cursor
(the editor's Agent, the Cursor CLI, or Cursor inside a JetBrains IDE
through AI Assistant): when you ask, the agent sends structured work
updates (decisions, progress, verification, blockers, questions, next steps
and the work you explicitly put off) for the project you approve. It never
sends prompts, replies, transcripts, tool output or files, and it needs no
API key. Oira is a remote MCP server; this package is the Oira skill plus
its address.

This is the Cursor package, version **0.11.0**, in the Agent Plugins 1.0
layout: `plugin.json`, `mcp.json` (the remote server) and
`skills/oira-work-reporting/` (`SKILL.md`, `references/` including
`setup-and-sign-in.md` and `client-surfaces.md`, and
`scripts/prepare_work_update.py`, the local preflight that runs before
every update; Python 3.11 or later, standard library only, no network).
The same skill, preflight and contract are used by the Claude Code, Codex,
Kiro and GitHub Copilot packages.

Requirements: a current Cursor editor, or the Cursor CLI (`agent`; native
Windows PowerShell, macOS, Linux and WSL installs), or AI Assistant in a
JetBrains IDE 2025.1 or later with the Cursor agent from its registry (a
paid Cursor plan); and Python 3.11 or later on the computer where the agent
runs. No Cursor surface is verified on a real host yet: the
[setup guide](https://oira-oira.com/coding-agent-help) shows the state of
each surface per operating system. Cloud Agents, self-hosted workers,
remote and container sessions, Bugbot, code review and mobile are not
supported.

## Install

### Editor: local plugin

Copy this whole folder to `~/.cursor/plugins/local/oira`
(`%USERPROFILE%\.cursor\plugins\local\oira` on Windows), then restart
Cursor or run **Developer: Reload Window**. In **Customize**, Oira's skill
appears under Skills and its server `oira` under MCP. Teams and Enterprise
workspaces may need local plugin imports allowed by an administrator. To
update, replace only this folder with the new release and reload. Do not
also copy the skill into a skills folder: one Oira installation per
computer.

### Editor, CLI or JetBrains: skill folder and MCP entry by hand

Use this route for the CLI, for Cursor through JetBrains AI Assistant, and
for older editors without a plugin loader.

1. Copy the whole `skills/oira-work-reporting` folder (with `references`
   and `scripts`) into your personal skills folder:
   `~/.cursor/skills/oira-work-reporting/` on macOS and Linux,
   `%USERPROFILE%\.cursor\skills\oira-work-reporting\` on Windows (or
   `.cursor/skills/oira-work-reporting/` inside one project, which changes a
   shared repository). Personal skills in `~/.cursor/skills` sync to Cloud
   Agents only if you turned that setting on; Oira is not qualified there.
2. Merge the Oira server into `~/.cursor/mcp.json` (personal) or the
   project's `.cursor/mcp.json`, keeping every other server:

       {
         "mcpServers": {
           "oira": {
             "url": "https://oira-oira.com/mcp"
           }
         }
       }

   A project entry overrides a personal entry of the same name; the MCP
   list in Cursor Settings shows which one is active. Never add headers, a
   client id, a secret or extra scopes: Oira uses dynamic client
   registration with PKCE and the scopes it advertises. Team MCP servers
   from the dashboard are not read by the CLI's ACP mode, so use these
   files for JetBrains.

## Sign in and set up

Editor: open Cursor Settings → MCP (or Customize → MCP), enable `oira` if
asked, and choose its login or authenticate action; finish in the browser.
CLI, from the project folder:

    agent --version
    agent mcp list
    agent mcp login oira
    agent mcp list-tools oira

The tool list must show the four `oira_*` tools. JetBrains: AI Chat → add
the Cursor agent from the registry, select it, then sign in to Oira from
that conversation the same way (the agent runs the CLI's ACP mode and reads
the `.cursor/mcp.json` files above). Your Cursor account login is not an
Oira sign-in. Then, in an Agent conversation in your project, send:

> Set up Oira for this project.

The agent picks the approved project with you, checks its local preflight,
tells you what Oira receives, and asks whether Oira should hear about this
repository only when you ask or at milestones in every chat. For the
second, it shows you a short block to paste into your personal User Rules
(Cursor Settings → Rules); it writes nothing itself, and nothing goes into
the repository, so teammates are never opted in. User Rules are documented
for the editor's Agent chats; whether the CLI or Cursor inside JetBrains
loads them is not verified, so ask per task there.

Then ask it to "Keep Oira updated on this task", "Share a progress update
for this project with Oira" or "Prepare and share a handoff for this project
with Oira". Updates are sent only when you ask, at milestones and
meaningful changes, never per prompt or in the background. Use Agent mode:
Ask or read-only modes cannot run the preflight or send an update.

The import of recent work is **not available for Cursor** in this version.
Current work is reported when you ask.

## If something is off

- The Oira tools are missing: the MCP list (Settings → MCP, or
  `agent mcp list`) must show `oira` enabled with four tools. A disabled
  server, a workspace allowlist of your team, or a stale project
  `.cursor/mcp.json` entry hides or overrides it. Oira never asks you to use
  `--approve-mcps` or to loosen team controls.
- Sign-in keeps repeating or used the wrong Oira account: sign in again
  from the same surface and disconnect the old connection in Oira.
- "Reporting is unavailable": the preflight needs Python 3.11 or later;
  `references/local-runtime.md` in the skill explains the shell details.
- Cursor also reads skills from Claude Code and Codex folders: if another
  app's Oira skill shows up, keep the one installed for Cursor and do not
  delete the other app's installation.
- More in the [setup and troubleshooting guide](https://oira-oira.com/coding-agent-help).

## Remove

Delete `~/.cursor/plugins/local/oira` (plugin route) or the skill folder and
the `oira` entry from the `mcp.json` you edited (manual route), remove the
Oira block from your User Rules, and disconnect the connection in Oira (a
local sign-out does not revoke it). Everything else in your Cursor
configuration stays as it was.

## What Oira receives

Oira receives only work updates you authorize, including decisions,
progress, blockers and deferred work. It does not collect your session
transcripts, tool output or source files, and you do not need to provide
API keys. The reporting workflow excludes credentials and filters recognized
secret patterns before sending an update; pattern checks cannot prove that
free text never contains a secret, so keep secrets out of what you ask your
agent to report. Read the [privacy policy](https://oira-oira.com/privacy)
and the [terms](https://oira-oira.com/terms). Support: nikita@oira-oira.com.
