# Claude Code project-local automatic capture

Automatic capture is an explicit, forward-only option. Do not configure it
unless `oira_connection_status` says it is enabled and returns a binding for
the exact Oira project label the user selected. The template requires Claude
Code 2.1.196 or later for stable prompt identity.

## Local privacy gate

Use only `<selected project root>/.claude/settings.local.json`. Never add an
active Oira content hook to the plugin package, user settings, project-shared
`.claude/settings.json`, or managed settings. Before writing in a Git project:

1. Resolve the exact selected repository or worktree root. A nested repository
   is a different scope.
2. Refuse automatic setup if `.claude/settings.local.json` is tracked by Git.
   Never put a project binding in a committed file.
3. Confirm the file is ignored; when needed, resolve the repository-local Git
   exclude file for that checkout (including linked-worktree indirection), add
   `/.claude/settings.local.json`, then verify it remains untracked.
4. Tell the user what the hooks send and wait for their yes: Claude Code's
   safety checks refuse this settings change without it. Then show the exact
   merge and preserve every unrelated setting or hook.
5. Claude Code applies the new hooks to the running session. If the next
   prompt does not reach Oira, ask the user to check that the three Oira hooks
   are listed in `/hooks` (Local Settings), or to start a new session in this
   folder. Never bypass the host's normal controls.

Do not copy the file into another repository, worktree, fork, imported project,
or member checkout. Remove it before copying the project directory. Configure
each intended local scope from a fresh Oira binding.

## Hook entries

Merge the entries below into the existing `hooks` object. Replace
`REPLACE_WITH_PROJECT_BINDING_HANDLE` with the binding returned for the exact
selected project. A plugin-bundled Claude MCP server uses the scoped server
name `plugin:oira:oira`.
The same mergeable object is packaged at
`../../../references/claude-project-settings-local.template.json` for
validation; it is a template, not an active plugin-global hook.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact|fork",
        "hooks": [
          {
            "type": "mcp_tool",
            "server": "plugin:oira:oira",
            "tool": "oira_capture_session_event",
            "input": {
              "event": {
                "schema": "plugin_hook_event.v1",
                "binding_handle": "REPLACE_WITH_PROJECT_BINDING_HANDLE",
                "client_session_key": "${session_id}",
                "event_type": "session_start",
                "identity_strength": "receive_time_only",
                "coverage": "forward_only_possible_gaps"
              }
            },
            "timeout": 3
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "mcp_tool",
            "server": "plugin:oira:oira",
            "tool": "oira_capture_session_event",
            "input": {
              "event": {
                "schema": "plugin_hook_event.v1",
                "binding_handle": "REPLACE_WITH_PROJECT_BINDING_HANDLE",
                "client_session_key": "${session_id}",
                "event_type": "user_prompt",
                "client_event_id": "${prompt_id}:user_prompt",
                "identity_strength": "stable_host_id",
                "content": "${prompt}",
                "host_prompt_id": "${prompt_id}",
                "coverage": "forward_only_possible_gaps"
              }
            },
            "timeout": 3
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "mcp_tool",
            "server": "plugin:oira:oira",
            "tool": "oira_capture_session_event",
            "input": {
              "event": {
                "schema": "plugin_hook_event.v1",
                "binding_handle": "REPLACE_WITH_PROJECT_BINDING_HANDLE",
                "client_session_key": "${session_id}",
                "event_type": "assistant_stop",
                "client_event_id": "${prompt_id}:assistant_stop",
                "identity_strength": "stable_host_id",
                "content": "${last_assistant_message}",
                "host_prompt_id": "${prompt_id}",
                "coverage": "forward_only_possible_gaps"
              }
            },
            "timeout": 3
          }
        ]
      }
    ]
  }
}
```

The template deliberately excludes `cwd`, transcript paths, tool arguments,
tool results, and Oira tool calls. Claude Code has no qualified native
user-interruption event in this release, so interruption coverage stays
unknown. A missing MCP connection or invalid/oversize event is non-blocking and
creates a possible coverage gap. Do not read a transcript to repair it.
