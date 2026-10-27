from .confirmation import request_closure, approve
from .models import Ticket, Approval
"""INTENTIONALLY VULNERABLE: repair this module in Exercises 3, 4 and 6."""
from .local_adapter import dispatch
from .models import AuditEvent

def execute(actor, proposal):
    # TODO: strict schema, allowlist, ownership, approval, safe audit trail.
    # EXERCISE 6: insert the two-line closure routing check here.
    result = dispatch(proposal["tool"], proposal.get("arguments", {}), actor)
    AuditEvent.objects.create(actor=actor, tool=str(proposal["tool"])[:40], outcome="unchecked_executed")
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

