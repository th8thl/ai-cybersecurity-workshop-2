# Set up the workshop

**You will work in `starter/`. `solution/` is the completed answer key;
leave it alone until the final comparison.**

Choose the instructions for where you will run the workshop:
- [GitHub Codespaces](GITHUB_CODESPACES_SETUP.md)
- [Your computer: Windows, macOS or Linux](LOCAL_SETUP.md)

Both instructions prepare `starter/` and install everything needed for the
exercises, including Bandit, Semgrep and NeMo. Codespaces also installs Ollama
and downloads Qwen automatically; the local instructions explain how to install it.

## Files created by setup
- `starter/.venv/`: the Python environment used to run the workshop.
- `starter/.env`: Django/model settings and any optional Gemini API key.
- `starter/db.sqlite3`: the local database containing synthetic workshop data.


Do not commit these files or enter real student data. Setup preserves existing
settings and passwords when you run it again.

## Website addresses and first use

- **Ticket list / landing page:** http://127.0.0.1:8000/tickets/
- **Create a ticket:** http://127.0.0.1:8000/tickets/new/
- **Ticket detail:** `/tickets/NUMBER/`, for example http://127.0.0.1:8000/tickets/5/
- **Optional assistant:** http://127.0.0.1:8000/chatbot/
- Opening http://127.0.0.1:8000/ takes you to the ticket list. Signing in also lands there unless you were opening a specific protected page.

In Codespaces use the same paths on your forwarded port 8000 website. Sign in as
`alice` using the password printed during setup. Click **New ticket**, enter a
**Request summary**, then click **Create ticket**. View and manage its status on
the resulting detail page. Use **Assistant** in the navigation when you want chat
help; ordinary ticket operations do not require a model or conversation.

Follow [Exercises](EXERCISES.md) for the classroom sequence. Some security tests
intentionally fail before repair; setup and connection errors are not intentional.

## Lost demo password
From `starter/`, with `.venv` activated, run:
```
python manage.py changepassword alice
```

## Verify setup without changing your workshop data
In the folder containing `manage.py`, with the existing Python environment active:
```
python scripts/verify_workshop.py
```
Before you change the code, this checks normal ticket use, existing protections, the known flaws and the code-scanner results. Do not use the default command to judge partially repaired code; follow the exercise-specific checkpoints.
Add `--semantic` to exercise local Qwen too. After completing the security repairs,
use `python scripts/verify_workshop.py --secured` to require the full security contract.

## Returning to the workshop another day

Setup is done once. On later days, activate the existing environment and start
the server using the command in your local or Codespaces guide. When using Qwen,
Ollama must also be running. Keep the existing environment and account passwords.

The assistant requires user consent. After signing in, open **Assistant →
Authorize assistant** and select permissions and a duration. The browser receives
the client's token, and the database stores its hash and authorization record.
When access expires or is revoked, authorize again; do not recreate the Python
environment or reset account passwords. Ordinary ticket pages remain available.
See [the consent flow](MCP_AUTHORIZATION.md).

## Opening links from chat
Every link inside the conversation opens in a new browser tab. Keep the chatbot tab open and switch back to it after inspecting a ticket. This applies to existing messages and newly received replies.
