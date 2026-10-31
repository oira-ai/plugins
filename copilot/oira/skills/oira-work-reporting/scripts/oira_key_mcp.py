"""Optional local MCP transport. Secrets enter through stdin and stay in the OS vault.

Install the adjacent key-requirements.txt into a private venv. This file is
rendered for one app/environment; it never chooses a remote from user input.
"""
from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
import getpass
import json
import logging
import os
from pathlib import Path
import re
import sys
import tempfile
from uuid import UUID

ORIGIN = 'https://oira-oira.com'
APP = 'copilot'
SCHEMA = 'oira_plugin_key.v1'
TOOLS = frozenset({
    'oira_connection_status', 'oira_submit_work_update', 'oira_work_update_status',
    'oira_finish_history_import', 'oira_bind_context_session', 'oira_revoke_context_session',
    'oira_check_context', 'oira_context_check_status', 'oira_cancel_context_check',
    'oira_context_interventions', 'oira_ack_context_intervention',
})


class KeySetupError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's default error quotes unexpected arguments, which could
        # include an accidentally supplied key. Accept secrets only on stdin.
        raise KeySetupError('invalid_arguments')


def host_for(secret):
    match = re.fullmatch(r'oira_k1\.([0-9a-f-]{36})\.[A-Za-z0-9_-]{43}', secret or '')
    if match is None:
        raise KeySetupError('installation_key_invalid')
    try:
        return str(UUID(match[1]))
    except ValueError:
        raise KeySetupError('installation_key_invalid') from None


def vault():
    # Same native-only policy as oira_runtime.credentials; no plaintext backend.
    try:
        if sys.platform == 'darwin':
            from keyring.backends.macOS import Keyring
        elif sys.platform == 'win32':
            from keyring.backends.Windows import WinVaultKeyring as Keyring
        elif sys.platform.startswith('linux'):
            from keyring.backends.SecretService import Keyring
        else:
            raise KeySetupError('credential_store_unavailable')
        instance = Keyring()
        if instance.priority <= 0:
            raise KeySetupError('credential_store_unavailable')
        return instance
    except Exception:
        raise KeySetupError('credential_store_unavailable') from None


def service():
    return f'oira.plugin-key.v1:{ORIGIN}:{APP}'


def metadata_path():
    return Path(__file__).resolve().parent.parent / 'references' / 'key-installation.json'


def read_metadata(path):
    try:
        if path.is_symlink() or path.stat().st_size > 4096:
            raise ValueError()
        value = json.loads(path.read_text(encoding='utf-8'))
        if (set(value) != {'schema', 'origin', 'app', 'host_uuid'}
                or value['schema'] != SCHEMA or value['origin'] != ORIGIN or value['app'] != APP
                or str(UUID(value['host_uuid'])) != value['host_uuid']):
            raise ValueError()
        return value
    except (OSError, ValueError, TypeError, KeyError):
        raise KeySetupError('installation_metadata_invalid') from None


def save_secret(secret, path, store):
    host = host_for(secret)
    if path.is_symlink():
        raise KeySetupError('installation_metadata_invalid')
    if path.exists() and read_metadata(path)['host_uuid'] != host:
        raise KeySetupError('installation_owner_conflict')
    try:
        store.set_password(service(), host, secret)
        if store.get_password(service(), host) != secret:
            raise KeySetupError('credential_store_unavailable')
    except Exception:
        raise KeySetupError('credential_store_unavailable') from None
    # Only nonsecret installation identity is written to disk. A failed metadata
    # write can be retried with the same key; it must not issue a new credential.
    path.parent.mkdir(parents=True, exist_ok=True)
    value = {'schema': SCHEMA, 'origin': ORIGIN, 'app': APP, 'host_uuid': host}
    fd, temporary = tempfile.mkstemp(prefix='.oira-key-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as file:
            json.dump(value, file)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return value


def load_secret(path, store):
    value = read_metadata(path)
    try:
        secret = store.get_password(service(), value['host_uuid'])
        if host_for(secret) != value['host_uuid']:
            raise KeySetupError('authentication_required')
        return secret
    except Exception:
        raise KeySetupError('authentication_required') from None


@asynccontextmanager
async def remote_session(secret):
    import httpx2
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client
    async with httpx2.AsyncClient(headers={'Authorization': 'Bearer ' + secret},
                                  timeout=30, follow_redirects=False) as http:
        async with streamable_http_client(ORIGIN + '/mcp', http_client=http) as streams:
            async with ClientSession(streams[0], streams[1], read_timeout_seconds=30) as remote:
                await remote.initialize()
                yield remote


async def login(secret):
    host = host_for(secret)
    async with remote_session(secret) as remote:
        result = await remote.call_tool('oira_connection_status')
        status = result.structured_content
        if status is None:
            texts = [block.text for block in result.content if getattr(block, 'type', '') == 'text']
            status = json.loads(texts[0]) if len(texts) == 1 else {}
        if result.is_error or status.get('host_authorization_uuid') != host:
            raise KeySetupError('installation_authentication_failed')
    return save_secret(secret, metadata_path(), vault())


def make_server(remote):
    from mcp.server import Server
    from mcp.types import CallToolResult, TextContent, ListToolsResult

    async def list_tools(context, params):
        try:
            result = await remote.list_tools()
        except Exception:
            return ListToolsResult(tools=[])
        # A bounded allowlist prevents an unrelated remote tool becoming part
        # of this integration. Preserve the server's canonical DTOs unchanged.
        result.tools = [tool for tool in result.tools if tool.name in TOOLS]
        result.next_cursor = None
        return result

    async def call_tool(context, params):
        if params.name not in TOOLS:
            return CallToolResult(is_error=True, content=[TextContent(type='text', text='operation_unavailable')])
        try:
            return await remote.call_tool(params.name, params.arguments or {})
        except Exception:
            # Transport exceptions may contain headers/URLs/input. Never put
            # their repr or traceback into model-visible tool output.
            return CallToolResult(is_error=True, content=[TextContent(type='text', text='oira_transport_unavailable')])

    return Server('oira-key', on_list_tools=list_tools, on_call_tool=call_tool)


async def serve():
    from mcp.server.stdio import stdio_server
    secret = load_secret(metadata_path(), vault())
    async with remote_session(secret) as remote:
        server = make_server(remote)
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())


def main():
    parser = Parser(description=__doc__)
    parser.add_argument('action', choices=('login', 'serve', 'forget-local'))
    parser.add_argument('--stdin', action='store_true')
    # SDK/HTTP debug logging must not expose credentials or request bodies.
    logging.disable(logging.CRITICAL)
    try:
        args = parser.parse_args()
        if not ORIGIN.startswith('https://') or APP not in {'codex', 'claude', 'kiro', 'copilot', 'cursor'}:
            raise KeySetupError('unrendered_package')
        if args.action == 'login':
            if not args.stdin and not sys.stdin.isatty():
                raise KeySetupError('interactive_secret_input_required')
            secret = (sys.stdin.readline(512).strip() if args.stdin and not sys.stdin.isatty()
                      else getpass.getpass('Oira installation key: '))
            import anyio
            result = anyio.run(login, secret)
            print(json.dumps({'authenticated': True, **result}))
        elif args.action == 'serve':
            import anyio
            anyio.run(serve)
        else:
            path = metadata_path()
            value = read_metadata(path)
            store = vault()
            if store.get_password(service(), value['host_uuid']):
                store.delete_password(service(), value['host_uuid'])
            path.unlink()
            print('{"local_credential_removed":true,"server_revocation":"unchanged"}')
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        code = str(exc) if isinstance(exc, KeySetupError) else 'key_setup_unavailable'
        print(json.dumps({'ok': False, 'error': code}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
