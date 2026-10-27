# Security decisions

- Ticket pages directly call the shared ticket service. The assistant uses MCP;
  its server calls the same service. Ownership and confirmation rules are shared.
- Signing into Django is separate from authorizing the assistant. Explicit user
  consent selects delegated permissions and a 1, 5 or 30 minute lifetime.
- Store only token hashes, owner, client, audience, permissions and lifecycle
  metadata in authorization records. Deliver the raw token to the client after
  consent; keep it out of prompts, tool arguments, logs and reports.
- Bind the client token to the signed-in user. MCP independently validates
  permission, client, audience, expiry and revocation before executing a tool.
- Present only granted tools to the model. Keep authorization outside the model.
- MCP can request closure but cannot confirm it. The ticket page requires human
  confirmation with the existing owner, expiry and one-use transaction checks.
- Keep real NeMo checks on input, tool request, tool result and final response.
  Keep structured response schemas, independent validation and bounded agent loops.
- Use actual stdio MCP initialization, discovery and calls. The educational
  consent flow is not a complete OAuth provider; distributed production should
  use a real provider and the MCP HTTP authorization specification.
- Scan the real application and test authorization and model-tool boundaries.
- The student code intentionally retains the validation, ownership, approval
  weaknesses identified in the exercises. User consent/token
  enforcement and NeMo integration are working infrastructure in both versions.
