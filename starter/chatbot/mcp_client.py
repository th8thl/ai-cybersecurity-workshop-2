"""MCP client presenting the user's delegated access token over local stdio."""
import asyncio
from contextlib import asynccontextmanager
from datetime import timedelta
import json
import os
import sys
from django.conf import settings
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from security.mcp_authorization import (current_access_token, require_authorization,
    MCPAuthorizationError, TOOL_SCOPES)

MODEL_TOOLS = set(TOOL_SCOPES)


def environment(token=None):
    env = {name:value for name,value in os.environ.items()
        if name.upper() in {'SYSTEMROOT','WINDIR','PATH','TEMP','TMP','USERPROFILE','HOME'}}
    env.update({'DJANGO_SETTINGS_MODULE':'support_portal.settings','DJANGO_SECRET_KEY':settings.SECRET_KEY,
        'WORKSHOP_RUNTIME_DB':str(settings.DATABASES['default']['NAME']),
        'MCP_ACCESS_TOKEN':token if token is not None else (current_access_token() or ''),
        'PYTHONUNBUFFERED':'1'})
    return env


@asynccontextmanager
async def connection(params):
    logs = settings.BASE_DIR/'results'
    logs.mkdir(exist_ok=True)
    with (logs/'mcp-service.log').open('a',encoding='utf-8') as errlog:
        async with stdio_client(params,errlog=errlog) as streams:
            yield streams


async def exchange(tool=None,arguments=None):
    params = StdioServerParameters(command=sys.executable,
        args=[str(settings.BASE_DIR/'mcp_server/server.py')],env=environment())
    async with connection(params) as (reader,writer):
        async with ClientSession(reader,writer,read_timeout_seconds=timedelta(seconds=30)) as session:
            initialized = await session.initialize()
            manifest = await session.list_tools()
            if tool is None:
                return {'protocol':initialized.protocolVersion,'server':initialized.serverInfo.name,
                    'tools':[{'name':t.name,'description':t.description,'inputSchema':t.inputSchema}
                             for t in manifest.tools if t.name in MODEL_TOOLS]}
            if tool not in {t.name for t in manifest.tools}:
                raise PermissionError('The MCP server does not offer that tool.')
            response = await session.call_tool(tool,arguments or {})
    if response.isError:
        raise PermissionError('The MCP server rejected this tool call.')
    data = response.structuredContent
    if data is None:
        data = json.loads(next((item.text for item in response.content if item.type=='text'),'{}'))
    if not isinstance(data,dict) or not data.get('ok'):
        if isinstance(data,dict) and data.get('code'):
            raise MCPAuthorizationError(data['error'],data['code'])
        raise PermissionError('This ticket or operation is not available to your account.')
    return data['data']


def call(actor,tool,arguments):
    if tool not in TOOL_SCOPES:
        raise PermissionError('The assistant cannot call that tool. Confirm closure on the ticket page.')
    require_authorization(actor,TOOL_SCOPES[tool])
    if getattr(settings,'MCP_TRANSPORT','stdio')=='inprocess-test':
        from tickets import ticket_service
        if tool=='list_tickets':return ticket_service.list_tickets(actor)
        return ticket_service.execute(actor,{'tool':tool,'arguments':arguments})
    try:
        return asyncio.run(exchange(tool,arguments))
    except PermissionError:
        raise
    except Exception as exc:
        raise RuntimeError('Could not communicate with the MCP server. Open Debug for the underlying error.') from exc


def discover(actor):
    grant = require_authorization(actor)
    if getattr(settings,'MCP_TRANSPORT','stdio')=='inprocess-test':
        return {'server':'unit-test service','tools':[{'name':name} for name in sorted(MODEL_TOOLS)
                if TOOL_SCOPES[name] in grant.scopes]}
    manifest = asyncio.run(exchange())
    manifest['tools'] = [tool for tool in manifest['tools'] if TOOL_SCOPES[tool['name']] in grant.scopes]
    return manifest
