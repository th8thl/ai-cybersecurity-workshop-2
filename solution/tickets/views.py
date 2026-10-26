"""HTTP views for the ticket system; no model or MCP dependency."""
import json
import logging
from datetime import timedelta
from uuid import UUID
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from .forms import TicketForm, TicketImportForm, AttachmentForm
from django.http import FileResponse, HttpResponse, JsonResponse
from .file_imports import load_ticket_file
from .attachments import save_attachment, open_attachment
from .models import Ticket, Approval, Attachment
from . import ticket_service
from .presentation import describe
from security.diagnostics import failure_details
from security.redaction import sanitize

logger = logging.getLogger(__name__)

@login_required
def ticket_list(request):
    return render(request, "tickets/ticket_list.html", {
        "tickets":Ticket.objects.filter(owner=request.user).order_by("-pk")})

@login_required
def ticket_create(request):
    form = TicketForm(request.POST if request.method == "POST" else None)
    error = None
    if request.method == "POST" and form.is_valid():
        try:
            result = ticket_service.execute(request.user, {"tool":"create_ticket", "arguments":{
                "title":form.cleaned_data["title"]}})
            messages.success(request, "Ticket created.")
            return redirect("ticket_detail",ticket_id=result["ticket_id"])
        except (PermissionError, RuntimeError, ValueError) as exc:
            logger.error("Ticket creation failed: %s", json.dumps(failure_details(exc)))
            error = sanitize(str(exc))
    return render(request,"tickets/ticket_create.html",{"form":form,"error":error})

@login_required
def ticket_detail(request, ticket_id):
    try:
        ticket = ticket_service.execute(request.user, {"tool":"get_ticket", "arguments":{"ticket_id":ticket_id}})
    except (PermissionError, Ticket.DoesNotExist, ValueError):
        return render(request,"tickets/ticket.html",{"unavailable":True},status=404)
    except RuntimeError as exc:
        logger.error("Ticket read failed: %s",json.dumps(failure_details(exc)))
        return render(request,"tickets/ticket.html",{"error":sanitize(str(exc))},status=503)
    error = None
    if request.method == "POST":
        try:
            action = request.POST.get("ticket_action")
            if action == 'attach':
                attachment_form = AttachmentForm(request.POST, request.FILES)
                if not attachment_form.is_valid():
                    raise ValueError(' '.join(str(message) for errors in attachment_form.errors.values() for message in errors))
                save_attachment(request.user, Ticket.objects.get(pk=ticket_id), attachment_form.cleaned_data['attachment'])
                messages.success(request, 'Attachment uploaded.')
            elif action == "close":
                result = ticket_service.execute(request.user,{"tool":"close_ticket","arguments":{"ticket_id":ticket_id}})
                messages.success(request,"Closure requested. Confirm below to close this ticket." if result.get("pending_approval") else describe(result,"close_ticket"))
            elif action in {"confirm","cancel"}:
                identifier=UUID(request.POST.get("approval_id", ""))
                if not Approval.objects.filter(pk=identifier,actor=request.user,ticket_id=ticket_id).exists():
                    raise PermissionError("Confirmation does not belong to this ticket and account.")
                if action == "confirm":
                    result = ticket_service.approve(request.user,identifier)
                    messages.success(request,describe(result,"confirm_close_ticket"))
                else:
                    ticket_service.cancel_confirmation(request.user,identifier,ticket_id)
                    messages.success(request,"Cancelled. Your ticket will stay open.")
            else:
                raise ValueError("Unknown ticket action.")
            return redirect("ticket_detail",ticket_id=ticket_id)
        except (PermissionError, ValueError, RuntimeError) as exc:
            logger.error("Ticket action failed: %s",json.dumps(failure_details(exc)))
            error = sanitize(str(exc))
    approvals=Approval.objects.filter(actor=request.user,ticket_id=ticket_id,consumed=False,
        created_at__gte=timezone.now()-timedelta(minutes=5),ticket__owner=request.user,ticket__status="open")
    return render(request,"tickets/ticket.html",{"ticket":ticket,"approvals":approvals,"error":error,
        "attachments":Attachment.objects.filter(ticket_id=ticket_id).order_by("created_at"),
        "attachment_form":AttachmentForm()})


@login_required
def ticket_import(request):
    form = TicketImportForm(request.POST or None, request.FILES or None)
    error = None
    if request.method == 'POST' and form.is_valid():
        try:
            data = load_ticket_file(form.cleaned_data['ticket_file'])
            result = ticket_service.execute(request.user, {'tool':'create_ticket', 'arguments':data})
            messages.success(request, 'Ticket imported. The new ticket belongs to your account.')
            return redirect('ticket_detail', ticket_id=result['ticket_id'])
        except (ValueError, PermissionError) as exc:
            error = str(exc)
    return render(request, 'tickets/ticket_import.html', {'form':form, 'error':error},
                  status=400 if request.method == 'POST' else 200)


@login_required
def ticket_import_template(request):
    response = JsonResponse({'title':'Registration help'})
    response['Content-Disposition'] = 'attachment; filename="ticket-template.json"'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@login_required
def ticket_export(request, ticket_id):
    try:
        ticket = ticket_service.execute(request.user, {'tool':'get_ticket', 'arguments':{'ticket_id':ticket_id}})
    except (PermissionError, Ticket.DoesNotExist, ValueError):
        return HttpResponse('This ticket is not available to your account.', status=404)
    response = JsonResponse({'title':ticket['title']})
    response['Content-Disposition'] = f'attachment; filename="ticket-{ticket_id}.json"'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@login_required
def attachment_download(request, ticket_id):
    try:
        ticket_service.execute(request.user, {'tool':'get_ticket', 'arguments':{'ticket_id':ticket_id}})
        ticket = Ticket.objects.get(pk=ticket_id)
        stream, filename = open_attachment(ticket, request.GET.get('name', ''))
    except (PermissionError, Ticket.DoesNotExist, FileNotFoundError, IsADirectoryError):
        return HttpResponse('This attachment is not available for this ticket.', status=404)
    except ValueError as exc:
        return HttpResponse(str(exc), status=400, content_type='text/plain; charset=utf-8')
    response = FileResponse(stream, as_attachment=True, filename=filename,
                            content_type='application/octet-stream')
    response['X-Content-Type-Options'] = 'nosniff'
    return response
