from django.conf import settings
import json
import logging
from datetime import timedelta
from uuid import UUID, uuid4
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from chatbot.ai_client import AIClientError
from tickets.models import Ticket, Approval, AuditEvent
from security.mcp_authorization import authorization_status, MCPAuthorizationError, PERMISSIONS
from .planner import plan
from .agent import run as run_agent
from guardrails.runtime import check, GuardrailBlocked
from security.redaction import sanitize
from .tool_policy import execute
from security.diagnostics import failure_details
from tickets.presentation import describe

logger = logging.getLogger(__name__)

def selected_provider(request):
    # Apply the new default once, including sessions that previously saved Demo.
    if request.session.get("qwen_default_applied") != 2:
        if request.session.get("action_provider") in {None, "mock"}:
            request.session["action_provider"] = "qwen"
        request.session["qwen_default_applied"] = 2
    return request.session.get("action_provider", "qwen")


def context(request):
    grant, authorization_error = authorization_status(request.user)
    history = sanitize(request.session.get("action_history", []))
    return {
        "history": history,
        "nemo_enabled": settings.NEMO_CHECKS,
        "nemo_mode": settings.NEMO_POLICY_MODE,
        "authorization":grant, "authorization_error":authorization_error,
        "permission_labels":[PERMISSIONS[p] for p in grant.scopes] if grant else [],
        "form_token": str(uuid4()),
        "tickets": Ticket.objects.filter(owner=request.user).order_by("-pk")[:3],
        "approvals": Approval.objects.filter(actor=request.user, consumed=False,
            created_at__gte=timezone.now()-timedelta(minutes=5), ticket__owner=request.user,
            ticket__status="open").select_related("ticket"),
        "events": AuditEvent.objects.filter(actor=request.user).order_by("-id")[:20],
        "selected_provider": selected_provider(request),
        "inspection": request.session.get("action_inspection", ""),
        "prompts": request.session.get("action_prompts", "Send a message to see the exact prompts used for each model step. Demo mode does not call a model."),
    }

@login_required
def chat(request):
    error = None
    result = None
    history = sanitize(list(request.session.get("action_history", [])))
    if request.method == "POST":
        token = request.POST.get("form_token")
        if token and token == request.session.get("last_action_submission"):
            if request.headers.get("Accept") == "application/json":
                data = context(request)
                return JsonResponse({"html":render_to_string("chatbot/chat.html",data,request=request),
                    "form_token":data["form_token"],"error":None,"prompts":data["prompts"]})
            return redirect("assistant")
        if token:
            request.session["last_action_submission"] = token
        provider = request.POST.get("provider", selected_provider(request))
        if provider not in {"mock", "qwen", "gemini"}:
            provider = "qwen"
        request.session["action_provider"] = provider
        message = request.POST.get("message", "").strip()[:2000]
        tool = ""
        trace = []
        prompts = []
        agent_completed = False
        proposal = None
        failure = None
        blocked_by_guardrail = False
        completed_history = None
        try:
            raw = request.POST.get("proposal", "").strip()
            if len(raw) > 4000:
                raise ValueError("The test proposal is too large.")
            if request.POST.get("ticket_action") == "close":
                identifier = int(request.POST["ticket_id"])
                message = f"Close ticket #{identifier}."
                proposal = {"tool":"close_ticket", "arguments":{"ticket_id":identifier}}
            elif raw:
                proposal = json.loads(raw)
                message = "Test a ticket request."
            else:
                turn = run_agent(request.user,message,provider,history,
                    request.session.get("last_ticket_id"),
                    planner=lambda message, provider, context: plan(message, provider, context=context, debug=prompts), trace=trace)
                reply, result, trace = turn["reply"], turn["result"], turn["trace"]
                tool = turn.get("tool", "")
                request.session["last_ticket_id"] = turn["last_ticket_id"]
                agent_completed = True
            if agent_completed:
                pass
            elif isinstance(proposal, dict) and set(proposal) == {"reply"} and isinstance(proposal["reply"], str):
                reply = proposal["reply"][:2000]
            else:
                result = execute(request.user, proposal, provider=provider, trace=trace)
                tool = proposal.get("tool", "")
                reply = describe(result, tool)
            if not agent_completed:
                check("output",sanitize(reply),provider,trace)
            request.session["action_inspection"] = json.dumps(sanitize({"trace":trace,"result":result}),indent=2)
            if proposal is not None:
                request.session["action_inspection"] = json.dumps(sanitize({"trace":trace,"proposal":proposal,"result":result}), indent=2)
        except MCPAuthorizationError as exc:
            error = str(exc)
        except GuardrailBlocked as exc:
            blocked_by_guardrail = True
            failure = failure_details(exc)
            error = sanitize(str(exc))
        except RuntimeError as exc:
            failure = failure_details(exc)
            logger.error("Ticket request failed: %s", json.dumps(failure))
            error = "Ticket request failed: " + sanitize(str(exc)) + " Open Debug below for diagnostic details."
        except (PermissionError, Ticket.DoesNotExist):
            error = "Request rejected. That ticket or confirmation is unavailable to your account."
        except AIClientError as exc:
            failure = failure_details(exc)
            logger.error("Model request failed: %s", json.dumps(failure))
            error = "Model request failed: " + sanitize(str(exc)) + " Open Debug below for diagnostic details."
        except (ValueError, KeyError, TypeError, ValidationError):
            error = "Request rejected. I couldn't safely complete that request. Try describing the ticket you need, or choose one from Your tickets."
        request.session["action_prompts"] = json.dumps(sanitize(prompts), indent=2) if prompts else (
            "Demo mode does not send a model prompt." if provider == "mock" else
            "No model prompt was sent. See the request trace for the stage that stopped this request.")
        if error:
            # A later model failure does not undo a completed tool operation.
            completed = [item for item in trace if "tool_result" in item]
            if completed and not blocked_by_guardrail:
                last = completed[-1]
                result, tool = last["tool_result"], last["tool"]
                completed_history = {"role":"assistant", "text":sanitize(describe(result,tool)),
                    "source":"ticket", "ticket_id":result.get("ticket_id")}
            request.session["action_inspection"] = json.dumps(sanitize({"trace":trace,"blocked":True,"provider":provider,"failure":failure}),indent=2)
            reply = error
            AuditEvent.objects.create(actor=request.user, tool="request", outcome="rejected")
        if message:
            history.append({"role":"user", "text":sanitize(message)})
        if completed_history:
            history.append(completed_history)
        history.append({"role":"error" if error else "assistant", "text":sanitize(reply),
            "error":bool(error), "source":"ticket" if result is not None and not error else "ai",
            "ticket_id":result.get("ticket_id") if result is not None and not error else None})
        if blocked_by_guardrail:
            history.append({"role":"assistant", "text":settings.CHATBOT_THEME.get("guardrail_reply",
                "I couldn’t complete that request safely. I can help with tickets you’re allowed to use. Please try a request about your own tickets, or use the Tickets page."),
                "source":"guardrail", "blocked":True, "error":False})
        request.session["action_history"] = history[-30:]
    data = context(request)
    data.update({"error":error, "result":json.dumps(result, indent=2) if result else ""})
    if request.method == "POST" and request.headers.get("Accept") == "application/json":
        return JsonResponse({"html":render_to_string("chatbot/chat.html", data, request=request),
            "form_token":data["form_token"], "error":error, "prompts":data["prompts"]})
    return render(request, "chatbot/chat.html", data)


