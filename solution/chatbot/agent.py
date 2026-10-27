"""Bounded model → authorized MCP tool → observation → model loop."""
import json
from django.conf import settings
from .mcp_client import discover, MODEL_TOOLS
from .planner import explicit_creation_request, ticket_request
from security.mcp_authorization import require_authorization, TOOL_SCOPES
from tickets.schema import validate_step, SCHEMA
from .tool_policy import execute
from tickets.presentation import describe
from guardrails.runtime import check
from security.redaction import sanitize

MAX_STEPS = 4
MAX_TOOL_CALLS = 3


def model_history(history):
    """Failed requests stay visible in the UI, but are not model examples."""
    completed = []
    for item in history:
        failed = item.get("error") or item.get("blocked") or item.get("role") == "error"
        if failed:
            if completed and completed[-1].get("role") == "user":
                completed.pop()
            continue
        completed.append(item)
    return [{"role":item.get("role","user"),"text":str(item.get("text",""))[:500]}
            for item in completed[-6:]]

def run(actor, message, provider, history, last_ticket_id=None, planner=None, trace=None):
    if planner is None:
        from .planner import plan
        planner = plan
    require_authorization(actor)
    message = sanitize(message)
    intent = ticket_request(message)
    creating = explicit_creation_request(message)
    if intent:
        require_authorization(actor, TOOL_SCOPES[intent["tool"]])
        if intent.get("latest"):
            require_authorization(actor, "tickets:read")
    trace = [] if trace is None else trace
    check("input", sanitize(message), provider, trace)
    manifest = discover(actor)
    trace.append({"mcp_initialize":{"server":manifest["server"],"protocol":manifest.get("protocol","unit-test"),"allowed_tools":[item["name"] for item in manifest["tools"]]}})
    observations = []
    seen = set()
    writes = 0
    last_result = None
    last_tool = None
    for index in range(MAX_STEPS):
        context = sanitize({"tools":manifest['tools'],"history":model_history(history),
            "observations":observations,"last_ticket_id":last_ticket_id})
        proposal = planner(message, provider, context=context)
        validate_step(proposal)
        trace.append({"step":index+1,"proposal":sanitize(proposal),"mcp_server":manifest['server']})
        if "reply" in proposal:
            # Retain the model's draft in Debug; it cannot report tool outcomes.
            reply = sanitize(describe(last_result, last_tool) if last_result is not None else proposal['reply'])
            check("output", reply, provider, trace)
            return {"reply":reply,"result":last_result,"trace":trace,"last_ticket_id":last_ticket_id,"tool":last_tool}
        if intent and "ticket_id" in intent and (proposal["tool"] != intent["tool"] or proposal["arguments"].get("ticket_id") != intent["ticket_id"]):
            raise ValueError("The model proposed a different ticket or operation than requested.")
        if creating and proposal["tool"] != "create_ticket":
            raise ValueError("The model proposed a different operation than the requested ticket creation.")
        if len(observations) >= MAX_TOOL_CALLS:
            raise ValueError("Agent tool-call budget reached.")
        fingerprint = json.dumps(proposal,sort_keys=True)
        if fingerprint in seen:
            raise ValueError("Repeated tool call blocked.")
        seen.add(fingerprint)
        if proposal['tool'] in {"create_ticket","close_ticket"}:
            writes += 1
            if writes > 1:
                raise ValueError("Only one write proposal is allowed per user turn.")
        result = execute(actor,proposal,provider=provider,trace=trace)
        observations.append({"tool":proposal['tool'],"result":result})
        trace.append({"tool":proposal["tool"],"tool_result":sanitize(result)})
        last_result = result
        last_tool = proposal["tool"]
        last_ticket_id = result.get('ticket_id',last_ticket_id)
        if result.get('pending_approval'):
            reply = f"Open the ticket page to confirm closure of ticket #{result['ticket_id']}."
            check("output",reply,provider,trace)
            return {"reply":reply,"result":result,"trace":trace,"last_ticket_id":last_ticket_id}
    raise ValueError("Agent reasoning-step budget reached.")
