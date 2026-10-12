# GitHub Copilot surfaces

One Oira connection covers every Copilot surface on a computer; the
surface changes only how Oira was installed and what to check, never what
is reported or who may report it. The connection is recorded as GitHub
Copilot whichever model Copilot runs. A Claude Code or Codex agent started
in the IDE's terminal is that app, with its own Oira package.

| Surface | How Oira gets there | What to check when tools are missing |
| --- | --- | --- |
| Copilot CLI (terminal, any OS) | plugin `oira@oira`, or the skill in `~/.copilot/skills` plus `~/.copilot/mcp-config.json` | `/mcp show oira` lists four tools; `/skills list` shows the skill; `/instructions` lists the personal file |
| VS Code, current Agent Host session | the CLI-installed plugin is discovered automatically; or Chat: Install Plugin From Source; portable `.mcp.json` and `~/.copilot/mcp-config.json` are read natively | Agent Plugins → Installed shows Oira; Configure Tools lists `oira` |
| VS Code, local extension-host session | same plugin or the skill in `~/.copilot/skills` plus `.vscode/mcp.json` (`servers` form) or MCP: Add Server | Configure Tools lists `oira`; the plugin and `/plugin` inventories are separate |
| JetBrains IDE, Copilot plugin (current, CLI-backed) | its Customizations/MCP UI and the format it writes, or the plugin inventory of the Copilot CLI it launches | the MCP tools panel shows `oira`; a 2025.2 or later IDE is required |
| JetBrains IDE, legacy Local harness | the skill attached by hand plus the `servers` MCP editor; skill discovery is not guaranteed | if the agent cannot read `references/` and `scripts/` or run the preflight, reporting is unavailable there |
| JetBrains AI Assistant, integrated Copilot agent | the skill by hand plus AI Assistant's own MCP list (Settings → Tools → AI Assistant → Model Context Protocol (MCP), `mcpServers` form with `url`), and **Pass custom MCP servers** enabled under Settings → Tools → AI Assistant → Agents; local projects only | the Oira tools inside that agent's conversation, not only the IDE's MCP list |
| Visual Studio 2026 18.5+ (Windows) | the skill in `%USERPROFILE%\.copilot\skills` plus a remote server added in the tools UI | the server's Auth action completed; Agent mode with terminal execution |

Not supported: the GitHub cloud coding agent, GitHub.com chat, pull-request
review, completions, inline edits, headless or prompt-mode runs, Eclipse
and Xcode until qualified. A package appearing in one of them does not make
reporting available there.

Windows runs natively in PowerShell (`py -3`); a Copilot inside WSL is a
Linux setup done inside WSL with its own skill, configuration and Python.
Remote or container sessions keep their own user profile: the preflight
must run where the skill's files are, and the sign-in must finish in the
approved client.
