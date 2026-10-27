# User consent and delegated MCP access

This workshop demonstrates a small consent-and-token flow inspired by OAuth.
It is not a complete OAuth provider. A user authorizes the assistant client to
use the MCP ticket server on their behalf, chooses permissions and sets a lifetime.

## The user-visible sequence

1. Sign in and use the ordinary ticket pages without authorizing the assistant.
2. Open **Assistant**, then **Authorize assistant**.
3. Choose **Read my tickets**, **Create tickets for my account**, and/or
   **Request closure of my tickets**. Choose 1, 5 or 30 minutes.
4. Click **Authorize assistant** or **Deny access**. Opening the page alone
   does not grant anything.
5. If approved, the client receives a random token for that user, that client,
   that MCP server and those permissions. Continue to the assistant.
6. **Manage assistant access** lets the user replace the authorization or revoke it.

New consent replaces the previous token for that user and client. Bob has his
own token and grant; changing Alice's authorization does not change Bob's.
Revocation or expiry stops subsequent tool calls. Existing conversation text
does not disappear, and the ordinary ticket pages continue to work.

## What is stored where?

| Location | Contents |
|---|---|
| `db.sqlite3`, model `chatbot.models.MCPAccessGrant` | User, client identifier, MCP audience, hash of the token, permissions, expiry and revocation time. The raw token is not stored in that record. |
| Browser's HttpOnly `mcp_access_token` cookie | The client's raw token, restricted to `/chatbot/`. Django reads it on assistant requests; JavaScript and the LLM do not receive it. |
| `.env` | Django configuration and optional model-provider API credentials. It does not hold a token for every user. |

The token is shown once after consent in **Inspect the token for the terminal
exercise**, so students can try the actual MCP client. It is not shown on later
page loads. Treat it as a password and omit it from reports and screenshots.
The consent response is not cached. No local encrypted credential store or
program passwords are needed for this flow.

## How an operation is checked

```text
Authenticated user approves permissions
        ↓
Assistant client receives that user's token
        ↓
Client starts the local MCP process with the token outside model arguments
        ↓
MCP validates token hash, client, audience, user, expiry, revocation and permission
        ↓
Ticket service checks the requested ticket and the authenticated owner
```

The current transport is stdio, so the token is passed in the private child
process environment as `MCP_ACCESS_TOKEN`. The server derives the user from the
grant record, never from a username or owner supplied by the LLM. The client
also binds the token to the current Django user and filters the tool list to
granted permissions. The server independently checks the permission when a tool
is called, including calls that bypass the normal client helper.

MCP offers reading, creation and requesting closure. **It does not offer a
confirmation tool.** Pending closure is reviewed and confirmed on the ticket
page by the signed-in user. No second service identity is involved.

## Files implementing the flow

- `chatbot/forms.py`: selectable permissions and duration.
- `chatbot/authorization_views.py`: consent, issuing the token and revocation.
- `chatbot/models.py`: persisted authorization records and token hashes.
- `security/mcp_authorization.py`: issuance, validation, user binding and token context.
- `chatbot/mcp_client.py`: supplies the token to MCP and limits discovered tools.
- `mcp_server/server.py`: validates each operation independently.
- `security/redaction.py`: removes token values from prompts and diagnostics.

Run `python manage.py migrate` when updating an existing copy. The migration
adds the authorization table without resetting accounts or tickets. Each user
must authorize the assistant; setup does not issue grants automatically.

Grant initial read access in [Exercise 1](EXERCISES.md#1-create-tickets-for-alice-and-bob) before the model request in Exercise 2. Follow [Exercise 7](EXERCISES.md#7-test-assistant-permissions-expiry-and-revocation)
for denial, read-only access, changed permissions, expiry and revocation. The
integration health check uses temporary users and explicitly created test grants;
it never changes a real user's consent.

## Production boundary

This is a first-party workshop simulation of consent and delegation. It does
not implement OAuth discovery, authorization-code exchange, PKCE or refresh tokens.
A distributed production deployment should use a real authorization provider,
the MCP HTTP authorization flow and HTTPS. Tokens must stay out of model context.
