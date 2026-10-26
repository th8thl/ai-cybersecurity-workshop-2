"""Client-side gate; MCP server repeats authoritative authorization independently."""
from tickets.schema import validate_proposal
from .mcp_client import call, MODEL_TOOLS
from guardrails.runtime import check
from security.mcp_authorization import require_authorization, TOOL_SCOPES
from security.redaction import sanitize

SECURE = True

def execute(actor, proposal, provider="mock", trace=None):
    if SECURE:
        validate_proposal(proposal)
    tool, arguments = proposal["tool"], proposal.get("arguments",{})
    if tool not in MODEL_TOOLS:
        raise ValueError("Tool is not available to the assistant.")
    require_authorization(actor, TOOL_SCOPES[tool])
    check("tool", sanitize(proposal), provider, trace)
    result = call(actor,tool,arguments)
    safe_result = sanitize(result)
    check("tool_result", safe_result, provider, trace)
    return safe_result
