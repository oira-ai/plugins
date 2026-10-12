<p align="center"><img src="codex/oira/assets/logo.png" width="96" alt="Oira"></p>

# Oira for Claude Code and Codex

[Oira](https://oira-oira.com) keeps your team's work current from the coding you
already do. This repository is the plugin marketplace for the Oira plugin in
Claude Code and Codex.

The **0.7.0** package source is public. Host-directory submission and
installed-client acceptance remain pending. No plugin credentials are embedded;
OAuth approval happens through Oira when a user connects the plugin.

Reporting needs **Python 3.11 or later** on the machine where the coding app
runs: before every update the plugin runs a small local check
(`scripts/prepare_work_update.py`, standard library only, no network) on the
exact update it is about to send.

This check reads only the candidate JSON on standard input (or the explicit
reference-generation arguments). It does not read environment variables,
credential files or authentication tokens. Secret names and URL patterns in
its source are used to reject sensitive update text, never to fetch or send
credentials. The coding app manages the separate Oira MCP OAuth connection;
the plugin does not ask for an API key.

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
projects this app may update and, if you want, turn on the import of your
recent work. The agent then checks the connection and the local preflight,
tells you what Oira will receive, and runs the import if you turned it on.

Then ask it to "Keep Oira updated on this task", "Share a progress update with
Oira" or "Prepare and share a handoff with Oira". It sends an update only when
you ask, at milestones and meaningful changes, never per prompt.

Earlier versions of this plugin could forward your prompts and replies through
project hooks and send past conversations. Oira no longer accepts either. If
your project still has old Oira hooks, ask your agent to remove them; it
removes only the Oira entries after you agree.

## What Oira receives

Oira receives only work updates you authorize, including decisions, progress,
blockers and deferred work. If you turn on the history import, your coding
agent reads your recent sessions in that project on your computer and sends
the same kind of updates about them. It does not collect your session
transcripts, tool output or source files, and you do not need to provide API
keys. The reporting workflow excludes credentials and filters recognized
secret patterns before sending an update.

Each update states facts about your work in an approved project: what you
decided, built, checked, are blocked on or put off for later, with the
repository, branch, commits and pull requests it involves. Updates from an
import are dated, and only work inside the period you chose is accepted. Oira checks
updates again before storing them. Pattern checks cannot prove that free text
never contains a secret, so keep secrets out of what you ask your agent to
report. Disconnect in Oira at any time to stop future updates.

Read the [privacy policy](https://oira-oira.com/privacy), the
[terms](https://oira-oira.com/terms) and the
[setup and troubleshooting guide](https://oira-oira.com/coding-agent-help).

## Support

Email nikita@oira-oira.com.

## License

[MIT](LICENSE)
