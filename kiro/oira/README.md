# Oira for Kiro

Keep [Oira](https://oira-oira.com) updated on your coding work from the Kiro
CLI or the Kiro IDE: when you ask, the agent sends structured work updates
(decisions, progress, verification, blockers, questions, next steps and the
work you explicitly put off) for the project you approve. It never sends
prompts, replies, transcripts, tool output or files, and it needs no API key.

This folder is the Kiro package, version **0.8.0**. Kiro has no plugin
directory for Oira, so it is installed by hand: one skill folder and one MCP
server entry. The same skill, preflight and contract are used by the Claude
Code and Codex packages in this repository.

- `skills/oira-work-reporting/`: the Agent Skill (`SKILL.md`, `references/`
  including `kiro-setup.md`, and `scripts/prepare_work_update.py`, the local
  preflight that runs before every update; Python 3.11 or later, standard
  library only, no network).
- `mcp.json`: the `mcpServers` entry to merge into your Kiro MCP settings.
- `agent.example.json`: the server, tool selector and skill resource to merge
  into an existing custom agent.

Requirements: a current Kiro (the CLI running the V3 engine, or the IDE
1.x; the IDE needs no CLI), Python 3.11 or later on the computer where Kiro
runs, and Git for the copy commands below (the IDE's skill import does not
need it). Qualified platforms are listed in the
[setup guide](https://oira-oira.com/coding-agent-help); cloud, SSH,
container, web and mobile Kiro sessions are not supported.

## Install

Use Terminal on macOS or Linux, or PowerShell on Windows (native Windows;
a Kiro inside WSL is a Linux setup done inside WSL). Check first:

    git --version
    python3 --version      # Windows: py -3 --version

CLI users can also confirm their build with `kiro-cli --version` (the V3
engine is chosen per session with `--v3` or saved as the default when Kiro
offers the switch). IDE users check the version under Kiro → About or
Check for Updates.

### 1. Copy the skill into your Kiro skills folder

macOS and Linux:

    git clone --depth 1 https://github.com/oira-ai/plugins.git "$HOME/.oira/plugins" || git -C "$HOME/.oira/plugins" pull --ff-only
    mkdir -p "$HOME/.kiro/skills/oira-work-reporting"
    cp -R "$HOME/.oira/plugins/kiro/oira/skills/oira-work-reporting/." "$HOME/.kiro/skills/oira-work-reporting/"
    ls "$HOME/.kiro/skills/oira-work-reporting"

Windows PowerShell:

    if (Test-Path "$env:USERPROFILE\.oira\plugins\.git") { git -C "$env:USERPROFILE\.oira\plugins" pull --ff-only } else { git clone --depth 1 https://github.com/oira-ai/plugins.git "$env:USERPROFILE\.oira\plugins" }
    New-Item -ItemType Directory -Force "$env:USERPROFILE\.kiro\skills\oira-work-reporting" | Out-Null
    Copy-Item -Recurse -Force "$env:USERPROFILE\.oira\plugins\kiro\oira\skills\oira-work-reporting\*" "$env:USERPROFILE\.kiro\skills\oira-work-reporting\"
    Get-ChildItem "$env:USERPROFILE\.kiro\skills\oira-work-reporting"

The listing must show `SKILL.md`, `references` and `scripts`. Run the same
commands again to update. In the Kiro IDE you can instead open Agent
Steering & Skills, choose **+ → Import a skill → GitHub** and paste
`https://github.com/oira-ai/plugins/tree/main/kiro/oira/skills/oira-work-reporting`
(the URL points at the skill folder, as Kiro requires); check that the
imported folder contains `references` and `scripts`, not only `SKILL.md`.
A workspace copy under `.kiro/skills/` works too and takes precedence.

### 2. Add the Oira server to your Kiro MCP settings

Merge the contents of `mcp.json` into `~/.kiro/settings/mcp.json` (user) or
`.kiro/settings/mcp.json` (workspace): if the file exists, add the `oira`
key inside your existing `mcpServers` object and keep every other server.
The `oauthScopes` are required; without them Kiro requests its default
OpenID scopes, which Oira refuses. Add no headers or credentials. The Kiro
IDE's MCP Servers panel edits the same file.

Custom agents load neither shared servers nor skills by themselves, and
selecting a server's tools does not load the server. Merge all three
entries of `agent.example.json` into your agent: the `oira` server under
its `mcpServers`, `@oira` in its `tools` (unless they already allow every
server) and the `skill://` resource in its `resources`, keeping its model,
prompt, permissions, hooks and other entries. If your agent already has
`includeMcpJson: true`, it takes the server from `mcp.json` and needs only
the tool entry and the resource. An `excludedTools` entry or a permissions
deny rule for `@oira` stays in force. Kiro CLI 2.x profiles accept
`file://` resources only: use
`file://~/.kiro/skills/oira-work-reporting/SKILL.md` there; the server
still comes from the profile's `mcpServers` or the shared `mcp.json`.

### 3. Sign in to Oira

Start a new Kiro chat in your project folder (restart Kiro if it was open).
In the CLI, type `/mcp`: `oira` shows a pending sign-in; press Enter on it
or run `/mcp auth oira` and finish in the browser. In the IDE, choose
Authenticate next to `oira` in the MCP panel. Your Kiro login and your Oira
sign-in are separate. `/mcp` commands are for the CLI; in the IDE use the
panel. This package needs no Kiro Power. Then send:

> Set up Oira for this project.

The agent picks the approved project with you, checks its local preflight,
tells you what Oira receives, and asks whether Oira should hear about this
repository only when you ask or at milestones in every chat. Only for the
second, and only after you agree, it adds a short instruction to your
personal steering file `~/.kiro/steering/oira-reporting.md`; nothing is
written to the repository, so teammates are never opted in by it.

Then ask it to "Keep Oira updated on this task", "Share a progress update
for this project with Oira" or "Prepare and share a handoff for this project
with Oira". Updates are sent only when you ask, at milestones and meaningful
changes, never per prompt or in the background.

The import of recent work is **not available for Kiro** in this version:
Kiro's session store is not a qualified source for it. Current work is
reported when you ask.

## Update

Repeat step 1 (it pulls the latest published package and copies it over the
installed skill). The MCP entry does not change between versions unless the
release notes say so. Start a new chat afterwards.

## If something is off

- The Oira tools are missing in a chat: check which agent is selected
  (`/agent list`); a custom agent needs the server entry, `@oira` and the
  `skill://` resource as in step 2. An administrator's MCP registry can
  also block the server.
- Sign-in keeps repeating or used the wrong account: `/mcp cancel-auth oira`,
  then `/mcp logout oira`, then sign in again.
- Registration fails with "Oira registers PKCE public clients only": keep
  `oauthScopes` and reconnect after the server fix. This is a registration
  compatibility error before consent; removing scopes or installing a
  Power will not fix it.
- "Reporting is unavailable": the preflight needs Python 3.11 or later;
  `references/local-runtime.md` in the skill explains the shell details.
- More in the [setup and troubleshooting guide](https://oira-oira.com/coding-agent-help).

## Remove

Remove the Oira block from `~/.kiro/steering/oira-reporting.md` (delete
the file only when nothing else is in it), remove the `oira` entry from
`mcp.json` and from any custom agent's `mcpServers`, `tools` and
`resources`, delete `~/.kiro/skills/oira-work-reporting`, and disconnect
the connection in Oira (local `/mcp logout` does not revoke it). Everything
else in your Kiro configuration stays as it was.

## What Oira receives

Oira receives only work updates you authorize, including decisions,
progress, blockers and deferred work. It does not collect your session
transcripts, tool output or source files, and you do not need to provide
API keys. The reporting workflow excludes credentials and filters recognized
secret patterns before sending an update; pattern checks cannot prove that
free text never contains a secret, so keep secrets out of what you ask your
agent to report. Read the [privacy policy](https://oira-oira.com/privacy)
and the [terms](https://oira-oira.com/terms). Support: nikita@oira-oira.com.
