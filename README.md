<p align="center"><img src="codex/oira/assets/logo.png" width="96" alt="Oira"></p>

# Oira for Claude Code and Codex

[Oira](https://oira-oira.com) keeps your team's work current from the coding you
already do. This repository is the plugin marketplace for the Oira plugin in
Claude Code and Codex.

The **0.6.1** package source is public. Host-directory submission and
installed-client acceptance remain pending. No plugin credentials are embedded;
OAuth approval happens through Oira when a user connects the plugin.

## Install

### Claude Code

Use **Terminal on macOS/Linux** or **PowerShell on Windows**, outside the Claude
chat box. Run these commands on the same computer and user account as Claude
desktop; for Windows desktop, use native PowerShell, not WSL.

First check the prerequisites:

    git --version
    claude --version

Both must print a version. If Git is missing, [install Git](https://git-scm.com/downloads).
If `claude` is missing, use [Anthropic's official installer](https://code.claude.com/docs/en/setup):

- macOS/Linux: `curl -fsSL https://claude.ai/install.sh | bash`
- Windows PowerShell: `irm https://claude.ai/install.ps1 | iex`

Follow the installer's PATH instructions, reopen the terminal and repeat the
checks. Installing Claude desktop alone may not put `claude` on your PATH.

Then run each command in order:

    claude plugin marketplace add https://github.com/oira-ai/plugins.git
    claude plugin install oira@oira --scope user
    claude plugin list --json

The source is public: no GitHub invitation is required. Wait for
`Successfully added marketplace: oira`, then `Successfully installed plugin:
oira@oira (scope: user)`. The final command must list `oira@oira`, user scope,
`enabled: true` and MCP URL `https://oira-oira.com/mcp`.

Quit and reopen Claude. In desktop, choose **Code**, open a **local** project
and check **+ → Plugins → Manage plugins**. In the terminal, start `claude`
from your project folder. Start a new chat for setup below. Cloud sessions do
not load the plugin installed on your machine. If pasting an install command
opens a plugin browser, return to your operating system's terminal.

For an existing installation, fetch the latest published version, then restart
Claude:

    claude plugin marketplace update oira
    claude plugin update oira@oira --scope user

If installed but disabled, run `claude plugin enable oira@oira --scope user`.

### Codex

**Codex.** Open Plugins, choose **+** and **Add a marketplace**, and enter
`oira-ai/plugins`. Then search for Oira and click **+**. From a
terminal, the same source is added with:

    codex plugin marketplace add oira-ai/plugins

If you have the macOS desktop app but no `codex` command, the
[Oira setup guide](https://oira-oira.com/coding-agent-help) includes a copyable
command that finds the app's bundled CLI. On Windows, use PowerShell and the
same user account as the desktop app. Install Git if cloning is unavailable.
Registration adds the source; install and enable **Oira** in Plugins, then
start a new chat. Existing sources can be refreshed with
`codex plugin marketplace upgrade oira`.

## Set up with one prompt

Start a new chat in your project folder and send:

> Set up Oira for this project.

Your coding agent asks you to sign in to Oira once. In the browser, choose the
projects this app may update and approve. The agent then checks the
connection, turns on automatic updates for that project (you approve the hook
it adds) and imports its recent history if you kept that option on.

Later you can ask it to "Share a progress update with Oira" or "Prepare and
share a handoff with Oira".

## What Oira receives

- Progress updates and handoffs your agent writes when you ask for them.
- With automatic updates on for an approved project: your prompts and the
  agent's final replies in that project, sent by a project-local hook you can
  inspect and remove.
- With the history import on: your prompts and the agent's final replies from
  that project's recent sessions, within the period you chose.

Oira never receives your files, tool calls, command output, credentials or
other projects, and it does not recover activity from times the app was
closed. Disconnect in Oira at any time to stop future updates.

Read the [privacy policy](https://oira-oira.com/privacy), the
[terms](https://oira-oira.com/terms) and the
[setup and troubleshooting guide](https://oira-oira.com/coding-agent-help).

## Support

Email nikita@oira-oira.com.

## License

[MIT](LICENSE)
