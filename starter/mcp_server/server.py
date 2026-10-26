"""Actual MCP server over stdio. Never put logging on protocol stdout."""
import os
import asyncio
import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "support_portal.settings")
import django
django.setup()
from mcp.server.fastmcp import FastMCP
from pydantic import StrictInt, StrictStr
from security.mcp_authorization import validate_token, MCPAuthorizationError
from tickets import ticket_service

server = FastMCP("Support portal ticket tools", log_level="WARNING")

def actor(scope):
    return validate_token(os.environ.get('MCP_ACCESS_TOKEN',''),scope).user

def perform(scope, tool, arguments):
    try:
        user = actor(scope)
        if tool == "list_tickets":
            result = ticket_service.list_tickets(user)
        else:
            result = ticket_service.execute(user, {"tool":tool,"arguments":arguments})
        return {"ok":True,"data":result}
    except MCPAuthorizationError as exc:
        return {'ok':False,'error':str(exc),'code':exc.code}
    except Exception as exc:
        logging.getLogger("ticket-service").warning("Denied operation: %s", type(exc).__name__)
        # Details must not expose credentials, paths or another user's records.
        return {"ok":False,"error":"Tool request denied or invalid."}

@server.tool()
async def list_tickets() -> dict:
    """List tickets belonging to the authenticated user. No user ID argument."""
    return await asyncio.to_thread(perform, "tickets:read", "list_tickets", {})

@server.tool()
async def get_ticket(ticket_id: StrictInt) -> dict:
    """Read one ticket belonging to the authenticated user."""
    return await asyncio.to_thread(perform, "tickets:read", "get_ticket", {"ticket_id":ticket_id})

@server.tool()
async def create_ticket(title: StrictStr) -> dict:
    """Create a support ticket for the authenticated user."""
    return await asyncio.to_thread(perform, "tickets:create", "create_ticket", {"title":title})

@server.tool()
async def close_ticket(ticket_id: StrictInt) -> dict:
    """Request closure. Secure policy returns a pending approval, not immediate closure."""
    return await asyncio.to_thread(perform, "tickets:propose-close", "close_ticket", {"ticket_id":ticket_id})

if __name__ == "__main__":
    try:
        server.run(transport="stdio")
    except KeyboardInterrupt:
        pass  # A manual Ctrl+C is a normal shutdown, not a server failure.
