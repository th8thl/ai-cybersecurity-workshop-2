"""Supplied approval infrastructure; Exercise 6 only changes dispatch routing."""
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models import Ticket, Approval, AuditEvent
from .local_adapter import dispatch


def request_closure(actor, ticket_id):
    """Create a pending approval for the actor's open ticket; do not close it."""
    with transaction.atomic():
        ticket = Ticket.objects.select_for_update().filter(pk=ticket_id, owner=actor).first()
        if ticket is None:
            raise PermissionError("Ticket unavailable to this user.")
        if ticket.status != "open":
            raise ValueError("Ticket is already closed.")
        approval = Approval.objects.create(actor=actor, ticket=ticket)
        AuditEvent.objects.create(actor=actor, tool="close_ticket", outcome="pending_approval")
        return {"pending_approval": str(approval.pk), "ticket_id": ticket.pk,
                "message": "Review the ticket and confirm using the approval form."}


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
