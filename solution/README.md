# Session 2 — Completed answer key

Code is organized into `support_portal/` (Django settings and main routes), `tickets/`
(ticket system), and `chatbot/` (optional assistant). See the
[code map and update instructions](../README.md#where-the-code-lives).

## Run the answer key in Codespaces

Students work in `starter/`. These commands are for instructors comparing the completed answer key. Codespaces automatically prepares only `starter/`, so create the answer key's environment once, from the repository root:

```bash
cd solution
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/configure.py
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 0.0.0.0:8001
```

Save the printed demo passwords. Open port **8001** in the Codespaces **Ports** panel and visit `/tickets/`.

For later runs, from `solution/`:

```bash
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8001
```

Activate this environment in each new answer-key terminal. Use the Python 3.12 or 3.13 interpreter supplied by the workshop Codespace.

## Qwen / Ollama
Codespaces installs/starts Ollama and downloads `qwen3:0.6b-q4_K_M` automatically.
Validate the model in the Codespaces terminal:
```bash
ollama pull qwen3:0.6b-q4_K_M
ollama list
```
Select **Qwen · local AI** in Assistant mode. **Demo · no model needed** needs no model or API key.
Gemini needs GEMINI_API_KEY and an available GEMINI_MODEL in this app's `.env`.

## Exercises and checks
The [student exercises](../docs/EXERCISES.md) are performed in application. To verify this completed answer key, run these commands from solution with its environment activated:
```bash
python manage.py test tests.test_ticket_portal
python manage.py test tests.test_chat_storage
python manage.py test tests.test_prompt_security
python manage.py test tests.test_approval
python scripts/run_sast.py
python guardrails/compare.py
```
All tests must pass.
Scanner results go to this app's ignored `results/`. Only Qwen/semantic NeMo checks need Ollama;
its policy verdict never grants application permission. The assistant at `/chatbot/` builds on the Session 1 security code.

## Integrated security checks
Users authorize the assistant through `/chatbot/authorization/`; setup does not issue user tokens.
Run `python scripts/healthcheck.py` to exercise real MCP and NeMo with disposable
data; add `--semantic` for live Qwen. See [scope and evidence](../docs/SCOPE_AND_EVIDENCE.md)
and [user consent and delegated access](../docs/MCP_AUTHORIZATION.md).

For all checks in one command, run `python scripts/verify_workshop.py`. Add
`--semantic` for local Qwen. Solution always expects the completed security controls; it does not need `--secured`. Health checks use disposable data and credentials.

## Conversation links
Links inside the conversation open in a new browser tab. For example, click **View ticket #…** in a Ticket result to inspect the ticket, then switch back to the original chatbot tab to continue. This also applies to links in newly received replies.

After signing in, open **Assistant → Authorize assistant** and choose permissions
and a duration. Ordinary ticket pages work independently. See
[consent, token storage, expiry and revocation](../docs/MCP_AUTHORIZATION.md).

## Start the MCP ticket server directly

With this folder's existing Python environment active, run from the folder
containing `manage.py`:

```bash
python mcp_server/server.py
```

The process waits for MCP messages through standard input/output. It does not
open a browser page or an HTTP port. Stop it with **Ctrl+C**. By itself, this
command does not supply a user's delegated access token, so it cannot access
tickets until an authorized client provides one.

For ordinary website use, no separate server command is needed: the application
starts the MCP process and supplies the user's token for each request. Follow the
[MCP exercise](../docs/EXERCISES.md#5-start-the-ticket-mcp-server-and-call-it-directly)
to discover the available tools.
The exercise client starts a new server process; it does not attach to the
terminal opened by the command above.

