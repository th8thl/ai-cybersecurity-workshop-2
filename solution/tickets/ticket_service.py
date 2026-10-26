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
                if ticket.status != "open":
                    raise ValueError("Ticket is already closed.")
                approval = Approval.objects.create(actor=actor, ticket=ticket)
                AuditEvent.objects.create(actor=actor, tool=tool, outcome="pending_approval")
                return {"pending_approval": str(approval.pk), "ticket_id": ticket.pk,
                        "message": "Review the ticket and confirm using the approval form."}
        result = dispatch(tool, args, actor)
        AuditEvent.objects.create(actor=actor, tool=tool, outcome="executed")
        return result

def approve(actor, approval_id):
    with transaction.atomic():
        approval = Approval.objects.select_for_update().filter(pk=approval_id, actor=actor,
            consumed=False, created_at__gte=timezone.now()-timedelta(minutes=5)).first()
        if approval is None:
            raise PermissionError("Approval unavailable, expired, or already used.")
        ticket = Ticket.objects.select_for_update().filter(pk=approval.ticket_id, owner=actor, status="open").first()
        if ticket is None:
            raise PermissionError("Ticket no longer available for this action.")
        # Conditional claim also prevents reuse if the database lacks row locks.
        if Approval.objects.filter(pk=approval.pk, consumed=False).update(consumed=True) != 1:
            raise PermissionError("Approval already used.")
        result = dispatch("close_ticket", {"ticket_id": ticket.pk}, actor)
        AuditEvent.objects.create(actor=actor, tool="close_ticket", outcome="approved_executed")
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

