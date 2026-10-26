"""Internal ticket storage operations, used behind server-side authorization.
The actual MCP protocol boundary is implemented in mcp_server/server.py.
"""
from .models import Ticket

def dispatch(tool, arguments, actor):
    if tool == "create_ticket":
        ticket = Ticket.objects.create(owner=actor, title=arguments["title"])
    elif tool in {"get_ticket", "close_ticket"}:
        ticket = Ticket.objects.get(pk=arguments["ticket_id"])
        if tool == "close_ticket":
            ticket.status = "closed"
            ticket.save(update_fields=["status"])
    else:
        raise ValueError("Unknown tool")
    return {"ticket_id": ticket.pk, "title": ticket.title, "status": ticket.status}
