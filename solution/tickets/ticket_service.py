from .confirmation import request_closure, approve
from .models import Ticket, Approval
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models import Ticket, Approval, AuditEvent
from .schema import validate_proposal
from .local_adapter import dispatch

def execute(actor, proposal):
    validate_proposal(proposal)
    tool, args = proposal["tool"], proposal["arguments"]
    with transaction.atomic():
        if tool != "create_ticket":
            ticket = Ticket.objects.select_for_update().filter(pk=args["ticket_id"], owner=actor).first()
            if ticket is None:
                raise PermissionError("Ticket unavailable to this user.")
            if tool == "close_ticket":
                return request_closure(actor, args["ticket_id"])
        result = dispatch(tool, args, actor)
        AuditEvent.objects.create(actor=actor, tool=tool, outcome="executed")
        return result



def list_tickets(actor):
    return {"tickets": [{"ticket_id":t.pk,"title":t.title,"status":t.status}
        for t in reversed(Ticket.objects.filter(owner=actor).order_by("-id")[:20])]}


def cancel_confirmation(actor, approval_id, ticket_id=None):
    query = Approval.objects.filter(pk=approval_id,actor=actor,consumed=False)
    if ticket_id is not None:
        query = query.filter(ticket_id=ticket_id)
    if not query.update(consumed=True):
        raise PermissionError("Confirmation unavailable to your account.")
    AuditEvent.objects.create(actor=actor,tool="close_ticket",outcome="cancelled")

