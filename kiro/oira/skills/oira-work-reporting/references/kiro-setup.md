# Oira in Kiro: what to check and where things live

Read this during "Set up Oira" and whenever a Kiro-specific question comes
up (sign-in, the selected agent, the personal steering file, removal). Kiro
installs Oira by hand: the skill folder plus one MCP server entry. Nothing
here changes the user's model, permissions, hooks or other servers.

This installation uses a skill and a remote MCP server; it does not install
a Kiro Power. Do not use Power discovery or activation to check whether
Oira is connected. Check the MCP server and its tools instead.

## Kiro login versus Oira sign-in

Kiro's own login (`kiro-cli login`, or the IDE account) is not an Oira
sign-in. Oira is a remote MCP server with its own OAuth: in the CLI, `/mcp`
lists `oira` and shows a pending sign-in URL; selecting it (or
`/mcp auth oira`) opens the browser. In the IDE, the MCP panel shows
Authenticate next to `oira`. `/mcp logout oira` removes only the stored Oira
sign-in; it does not revoke the connection in Oira (see "Removal").

The `/mcp` commands above belong to Kiro CLI. In the IDE use the MCP panel;
typing those commands into IDE chat may only ask the agent to discuss them.
Keep the two `oauthScopes` in the server entry. Removing them does not bypass
Dynamic Client Registration. If the log says registration was rejected
with `Oira registers PKCE public clients only`, sign-in failed at the server
before consent; reconnect after the Oira server fix instead of adding a
client secret, changing the URL or removing scopes.

### Browser returns to a closed local callback

Kiro IDE 1.2.56 gives the whole connection, including browser sign-in,
60 seconds by default. If that time expires, it stops the local callback
server. A browser returning afterwards shows "Can't connect to the server"
even when Oira approval succeeded. The packaged server entry sets
`"timeout": 300000` (milliseconds) to allow five minutes.

If the log says `connection timed out after 60000ms`, add or update that
property inside the active `oira` entry. Check workspace settings and
the selected custom agent too: their server entry can override the user
settings. Keep the URL, scopes and other servers as they are. In the IDE,
reconnect `oira` in the MCP panel, choose Authenticate, and finish the
new browser flow within five minutes. In the CLI, cancel the pending auth
with `/mcp cancel-auth oira`, then use `/mcp auth oira` again.
Use the new sign-in tab; reloading the old local callback cannot
restart Kiro's listener. If the new flow still fails, check its new log
before changing other settings. Do not share callback URLs, codes or tokens.

An administrator's MCP registry or governance policy can block the server;
if `oira` is absent from `/mcp` although `mcp.json` names it, say so and
stop. Do not work around it.

## Where the pieces are

| Piece | Location |
| --- | --- |
| Skill (this folder) | `~/.kiro/skills/oira-work-reporting/` (user) or `.kiro/skills/oira-work-reporting/` (workspace); workspace wins on a name clash |
| MCP server entry | `~/.kiro/settings/mcp.json` (user) or `.kiro/settings/mcp.json` (workspace), key `oira`, `url` plus `oauthScopes` `connection_status:read` and `work_updates:write`, and `timeout: 300000` (milliseconds); or inside the selected agent's own `mcpServers` |
| Personal reporting instruction | `~/.kiro/steering/oira-reporting.md` |
| Custom agents | `~/.kiro/agents/` (global) and `.kiro/agents/` (workspace), JSON or Markdown with YAML front matter |

Skill folders need `SKILL.md`, `references/` and `scripts/`: if
`scripts/prepare_work_update.py` is missing, the import or copy was
incomplete and reporting is unavailable until the folder is complete.
Reporting needs Python 3.11 or later on this computer, never the Kiro CLI:
the IDE connects through its own MCP and skills panels.

## The selected agent must load Oira

The default agent loads workspace and user skills and the shared `mcp.json`
servers. A custom agent (IDE 1.x, CLI V3) loads neither by itself, and
three separate settings decide whether it reaches Oira. Selecting a
server's tools does not load the server:

1. The server: an `oira` entry under the agent's own `mcpServers` (the
   package's `agent.example.json` holds the exact entry), or
   `includeMcpJson: true`, which takes every server from the shared
   `mcp.json`. Suggest `includeMcpJson` only when the user already wants
   that scope.
2. The tool: `@oira` in the agent's `tools` (not needed when they already
   allow every server, for example `*` or `@mcp`).
3. The skill: `skill://~/.kiro/skills/oira-work-reporting/SKILL.md` (or a
   glob covering it) in the agent's `resources`.

An `excludedTools` entry or a permissions deny rule for `@oira` wins over
all of this; do not ask to loosen it. (`allowedTools` in CLI 2.x profiles
is legacy pre-approval, not an exclusion.)

When the Oira tools are missing in a chat, this is the first thing to check:
ask which agent is selected (`/agent list`, `/agent swap <name>`), then show
the three entries above as a merge into that agent's file. Never create a
new "Oira agent", switch the user's agent for them, or rewrite their file.

Kiro CLI 2.x profiles (the V2 engine) accept `file://` resources only:
there, `file://~/.kiro/skills/oira-work-reporting/SKILL.md` loads the skill
text, and the default agent reaches the skill as `/oira-work-reporting`.
The server still has to come from the profile's own `mcpServers` or the
shared `mcp.json`; the resource does not load it. Those profiles keep their
`allowedTools`, `toolAliases` and hooks as they are; `/upgrade-agent` is
the user's decision, not part of Oira setup.

## The personal reporting instruction

When the user chooses reporting in every chat, the block from SKILL.md goes
into `~/.kiro/steering/oira-reporting.md`. Create the file with this front
matter at the very top, then the block:

```
---
inclusion: always
---
```

Keep anything already in the file. The file is the user's own: it never
reaches teammates, and a workspace `.kiro/steering/` file must not be used
for this, because it would opt in everyone who opens the repository.

Custom agents read steering only through their `resources`
(`file://~/.kiro/steering/**/*.md` or the exact file); the default IDE
agent reads global steering by itself. Tell the user which case applies to
their agent, and that a Kiro CLI session that does not load global steering
needs the resource entry. If you cannot verify that the selected agent loads
the file, say so instead of claiming it will report.

## Removal

To stop reporting from this computer: remove the Oira block from
`~/.kiro/steering/oira-reporting.md` (delete the file only when nothing
else is in it), remove the `oira` entry from `mcp.json` and from any custom
agent's `mcpServers`, `tools` and `resources`, and delete the skill folder
`~/.kiro/skills/oira-work-reporting`. Ask the user to disconnect the
connection in Oira as well: a local `/mcp logout oira` or a deleted entry
does not revoke the grant Oira holds. Leave every other steering file,
server, skill, agent and sign-in untouched; a differently named Oira
package on the same computer (its own server key, skill folder and steering
file) is not part of this removal.
