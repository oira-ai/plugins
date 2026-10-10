# Codex project-local automatic capture

Automatic capture is an explicit, forward-only option. Do not configure it
unless `oira_connection_status` says it is enabled and returns a binding for
the exact Oira project label the user selected.

## Local privacy gate

Use only `<selected repo root>/.codex/hooks.json`. Never add an active Oira
content hook to the plugin package, `~/.codex`, a parent repository, or a
shared/managed configuration. Before writing in a Git repository:

1. Resolve the exact selected repository or worktree root. A nested repository
   is a different scope.
2. Refuse automatic setup if `.codex/hooks.json` is tracked by Git. Never put a
   project binding in a committed file.
3. Resolve the repository-local Git exclude file for that checkout (including
   linked-worktree indirection), add `/.codex/hooks.json`, then verify the file
   remains untracked.
4. Tell the user what the hooks send and wait for their yes: Codex's safety
   review refuses this file change without it. Then show the exact merge and
   preserve every unrelated hook.
5. Tell the user where to trust the hooks, because Codex runs no new or
   changed hook until it is trusted. In the Codex app: Settings, then Hooks,
   then Trust on each of the four Oira hooks listed under this project (Reload
   hooks if they are missing). The Codex CLI asks at its next start: Trust all
   and continue. The hooks run from the next chat in this folder. Never bypass
   hook trust.

Do not copy the file into another repository, worktree, fork, imported project,
or member checkout. Remove it before copying the project directory. Configure
each intended local scope from a fresh Oira binding.

## Hook entries

Merge the entries below into the existing `hooks` object. Replace
`REPLACE_WITH_PROJECT_BINDING_HANDLE` with the binding returned for the exact
selected project. The MCP server name is `oira`.
The same mergeable object is packaged at
`../../../references/codex-project-hooks.template.json` for validation; it is
a template, not an active plugin-global hook.

```json
{
  "description": "Explicit project-local Oira forward capture.",
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [
          {
            "type": "mcp_tool",
            "server": "oira",
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
            "server": "oira",
            "tool": "oira_capture_session_event",
            "input": {
              "event": {
                "schema": "plugin_hook_event.v1",
                "binding_handle": "REPLACE_WITH_PROJECT_BINDING_HANDLE",
                "client_session_key": "${session_id}",
                "event_type": "user_prompt",
                "client_event_id": "${turn_id}:user_prompt",
                "identity_strength": "stable_host_id",
                "content": "${prompt}",
                "host_turn_id": "${turn_id}",
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
            "server": "oira",
            "tool": "oira_capture_session_event",
            "input": {
              "event": {
                "schema": "plugin_hook_event.v1",
                "binding_handle": "REPLACE_WITH_PROJECT_BINDING_HANDLE",
                "client_session_key": "${session_id}",
                "event_type": "assistant_stop",
                "client_event_id": "${turn_id}:assistant_stop",
                "identity_strength": "stable_host_id",
                "content": "${last_assistant_message}",
                "host_turn_id": "${turn_id}",
                "coverage": "forward_only_possible_gaps"
              }
            },
            "timeout": 3
          }
        ]
      }
    ],
    "Interrupt": [
      {
        "hooks": [
          {
            "type": "mcp_tool",
            "server": "oira",
            "tool": "oira_capture_session_event",
            "input": {
              "event": {
                "schema": "plugin_hook_event.v1",
                "binding_handle": "REPLACE_WITH_PROJECT_BINDING_HANDLE",
                "client_session_key": "${session_id}",
                "event_type": "interrupt",
                "client_event_id": "${turn_id}:interrupt",
                "identity_strength": "stable_host_id",
                "host_turn_id": "${turn_id}",
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
tool results, and Oira tool calls. A missing MCP connection or invalid/oversize
event is non-blocking and creates a possible coverage gap. Do not read a
transcript to repair it.
