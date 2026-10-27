# Session 2 — Completed answer key

Code is organized into `support_portal/` (Django settings and main routes), `tickets/`
(ticket system), and `chatbot/` (optional assistant). See the
[code map and update instructions](../README.md#where-the-code-lives).

## Start the configured answer key

After completing this folder's initial setup, run from `solution/` in Windows
PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python manage.py runserver 127.0.0.1:8001
```

Open [the answer key's tickets](http://127.0.0.1:8001/tickets/).
Use this folder's own configured environment. For first-time installation, see
**Local setup** below. Students should use the application in `starter/` on port
8000 as described in [its README](../starter/README.md).


Students work in `starter/`. The steps below are only for an instructor who
wants to run the completed answer key for comparison.

Instructor reference with schema validation, ownership, approval and audit controls.
The answer key builds on the defended Session 1 chatbot.

## Local setup — run inside this folder
Use Python **3.13** for the Windows commands below. NeMo does not support
Python 3.14. Before setup, run `py -3.13 --version`; it must report Python 3.13.x.
If that command is unavailable, install Python 3.13 before continuing.

Windows PowerShell (for a new environment):
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/configure.py
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8001
```
If `.venv` already exists, check its Python version before proceeding; do not
rerun environment creation over an existing Python 3.14 environment.

On macOS/Linux use `python3.13 -m venv .venv` and `source .venv/bin/activate`;
the remaining commands are the same. Save Alice/Bob's printed passwords.
Open http://127.0.0.1:8001/tickets/ and sign in. The ticket list is the landing page. Create and manage requests directly; use Assistant in the navigation for optional chat.
Codespaces automatically prepares `starter/` only. To run this answer key in
Codespaces, use the setup commands above from `solution/`, activate with
`source .venv/bin/activate`, and bind runserver to `0.0.0.0:8001`.

The single `requirements.txt` installs the app, Bandit, Semgrep and NeMo in this
environment. These scripts and guardrails belong to the answer key. See [local setup](../docs/LOCAL_SETUP.md) for platform details.

## Qwen / Ollama
Codespaces installs/starts Ollama and downloads `qwen3:0.6b-q4_K_M` automatically.
Locally, install Ollama from https://ollama.com/download, start it, then run:
```
ollama pull qwen3:0.6b-q4_K_M
ollama list
```
Select **Qwen · local AI** in Assistant mode. **Demo · no model needed** needs no model or API key.
Gemini needs GEMINI_API_KEY and an available GEMINI_MODEL in this app's `.env`.

## Exercises and checks
The [student exercises](../docs/EXERCISES.md) are performed in application. To verify this completed answer key, run these commands from solution with its environment activated:
```
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
Links inside the conversation open in a new browser tab. For example, click **Open ticket #…** in a Ticket result to inspect the ticket, then switch back to the original chatbot tab to continue. This also applies to links in newly received replies.

After signing in, open **Assistant → Authorize assistant** and choose permissions
and a duration. Ordinary ticket pages work independently. See
[consent, token storage, expiry and revocation](../docs/MCP_AUTHORIZATION.md).

## Start the MCP ticket server directly

With this folder's existing Python environment active, run from the folder
containing `manage.py`:

```text
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

