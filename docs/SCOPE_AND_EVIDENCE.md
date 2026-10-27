# Session 2 scope and executable evidence

This checklist distinguishes application functionality from teaching discussion.

| Requirement | Implementation | How to verify |
|---|---|---|
| Structured outputs | Discovered MCP input schemas and a constrained action/reply JSON schema supplied to Qwen/Gemini; strict application validation | tickets/schema.py, chatbot/planner.py; malformed/extra-field tests |
| Secure coding | Ownership, CSRF, escaped output, redaction and regression tests | tests/test_ticket_access.py, tests/test_validation.py and tests/test_approval.py and test_interface.py; application rescan |
| Delegated access lifecycle | Explicit user consent; random tokens, hashes in DB, permission selection, expiry, replacement and revocation | tests/test_authorization.py; real MCP token rejection checks |
| Least privilege | Read-only tokens cannot create; model sees granted tools; MCP has no confirmation tool | Client-discovery tests and independent server-side scope checks |
| Agent/tool authorization | Bounded loop with tool observations, prior conversation and ticket context; duplicate-call/write limits | chatbot/agent.py; multi-step and budget tests |
| Actual MCP boundary | SDK stdio client/server; initialize, tools/list, tools/call; independent server authorization | mcp_server/server.py; scripts/healthcheck.py reports negotiated protocol |
| NeMo continuity | Real NeMo Colang runtime in the application on input, tool request, tool result and response | Exercise 9 configures policy.py, runtime.co and runtime.yml; tests/test_nemo.py uses the actual worker; compare.py --configured checks seven cases |
| OWASP/CWE | Worked findings, classifications, evidence and remediation mapping | SECURITY_FINDINGS.md; finding.schema.json and student report |
| SAST integration | Bandit/Semgrep inspect model-dispatch and application code; automated scan assertions and GitHub CI | scripts/verify_sast.py; .github/workflows/security.yml |

## Lab boundaries

Consent and delegated access tokens are implemented by the workshop application.
This is a small OAuth-style demonstration, not a complete OAuth provider. The
database stores hashes and grant metadata; the browser stores the client's raw
token in an HttpOnly cookie. Server/provider configuration remains in .env.
The MCP transport is a local stdio child process, with the token outside model
arguments. Remote production authorization is discussed, not implemented here.

Ordinary ticket pages do not require an assistant grant,
model, NeMo worker or MCP process. NeMo remains on the assistant's four content
boundaries. Its verdict does not grant ticket ownership or confirmation authority.
