# Session 2 — student working code

Code is organized into `support_portal/` (Django settings and main routes), `tickets/`
(ticket system), and `chatbot/` (optional assistant). See the
[code map and update instructions](../README.md#where-the-code-lives).

## Start the application after initial setup

Open port **8000** in the Codespaces **Ports** panel, then visit `/tickets/`. Keep this terminal running;
Ctrl+C stops the website. Assistant actions start the MCP server automatically. Ordinary ticket pages use the shared ticket service directly.

**Codespaces:** from the repository root:

```bash
cd starter
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

Open port **8000** in the **Ports** panel, then visit `/tickets/`.

First time running the project? Complete [Codespaces setup](../docs/GITHUB_CODESPACES_SETUP.md) first.


Run and repair the code in this folder. `solution/` is the instructor's answer key; you do not need to configure or run it.

1. Complete **one** setup guide: [GitHub Codespaces](../docs/GITHUB_CODESPACES_SETUP.md).
2. Follow [the exercise walkthrough](../docs/EXERCISES.md) in order. It gives the login procedure, exact inputs, code changes, test commands, expected results and evidence to record.
3. Keep your notes in a copy of [Student evidence](../docs/NOTES_TEMPLATE.md).

Open port **8000** in the Codespaces **Ports** panel and visit `/tickets/`. Use **New ticket** to create a request and open it to manage its status. **Assistant** in the navigation opens the optional chatbot at `/chatbot/`. Enter sends a message; Shift+Enter adds a line. Conversation links open new tabs. Debug shows the actual model prompts, tool requests and errors.

**Demo · no model needed** requires no model download or API key. **Qwen · local AI** requires Ollama and the model prepared by your setup guide. Both modes use the real ticket server and NeMo runtime.

All dependencies, including scanners and NeMo, are in this folder's `requirements.txt`. Your existing environment is used for both the website and exercise commands. Do not create extra environments for individual exercises.

Some security tests intentionally fail before the repairs. Connection errors and missing dependencies are not intentional failures. Use the exercise-specific commands: the default health check expects the original flaws to be present. After your repairs, use `--secured` so it expects those flaws to be fixed.

Returning another day? See [Returning to the workshop](../docs/SETUP.md#returning-to-the-workshop-another-day). Keep `.env`, `.venv/` and database files out of submissions and Git.

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

