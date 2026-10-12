# Cursor surfaces

One Oira connection covers every Cursor surface on a computer; the surface
changes only how Oira was installed and what to check, never what is
reported or who may report it. The connection is recorded as Cursor
whichever model Cursor runs. A Claude Code or Codex agent started in
Cursor's terminal is that app, with its own Oira package.

| Surface | How Oira gets there | What to check when tools are missing |
| --- | --- | --- |
| Cursor editor, Agent | the local plugin under `~/.cursor/plugins/local/oira`, or the skill in `~/.cursor/skills` plus `~/.cursor/mcp.json` | Customize shows the skill and `oira` enabled with four tools; Agent mode selected |
| Cursor CLI (`agent`, any OS) | the skill in `~/.cursor/skills` plus `~/.cursor/mcp.json` (the CLI reads the editor's configuration; plugin discovery is not relied on) | `agent mcp list` shows `oira` enabled; `agent mcp list-tools oira` lists four tools |
| JetBrains IDE, Cursor through AI Assistant (ACP) | the skill and `.cursor/mcp.json` (project or personal) readable by the registry-launched Cursor runtime; dashboard Team MCP servers are not read there | the Oira tools inside the Cursor-driven conversation, not only the IDE's MCP list; sign-in completed from that conversation |

Not supported: Cloud Agents, self-hosted workers, remote SSH or container
sessions, headless runs, Bugbot, code review and mobile. A skill synced to
Cloud Agents does not make reporting available there.

Windows runs natively in PowerShell (`py -3`); a Cursor CLI inside WSL is a
Linux setup done inside WSL with its own skill, configuration and Python.
The JetBrains runtime may be a managed binary rather than the `agent` on
the user's PATH: check the version and configuration it actually uses
before concluding that an entry is missing.
