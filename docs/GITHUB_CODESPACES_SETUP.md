# GitHub Codespaces setup

**Work in `starter/`. `solution/` is the completed answer key and does not need setup.**

## 1. Open the repository
Use the Session 2 folder as the GitHub repository root, with `.devcontainer/` at
the top level. Create a new Codespace and wait for post-create setup to finish.
It automatically:

1. Creates `starter/.venv`, the Python environment for the workshop.
2. Installs `starter/requirements.txt`, including Bandit, Semgrep and NeMo.
3. Creates `starter/.env`, generates a Django key and prepares the demo database.
4. Installs/starts Ollama and downloads `qwen3:0.6b-q4_K_M`.

Each user grants assistant access after signing in through **Assistant →
Authorize assistant**. See [the consent and token flow](MCP_AUTHORIZATION.md).

Save the printed Alice/Bob passwords for signing into the workshop. Downloads
can take several minutes. Wait for **Setup complete**. Ollama starts automatically
on later Codespace restarts. Ports 8000/8001 are private; 11434 is not forwarded.

## 2. Start the application
From the repository root:
```bash
cd starter
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```
Open port **8000** in the **Ports** panel and use `/tickets/` on that website. Sign in with username `alice` and the password printed after `alice password:`. Follow [Exercise 1](EXERCISES.md#1-create-tickets-for-alice-and-bob) for the complete login and first-ticket walkthrough. Start with **New ticket** on the ticket list. For chat exercises open **Assistant**, choose **Demo · no model needed** first, then **Qwen · local AI**.

## 3. Run tools and exercises
In a second terminal, `cd starter` and `source .venv/bin/activate`:
```bash
python manage.py test tests.test_ticket_portal
python manage.py test tests.test_chat_storage
python manage.py test tests.test_prompt_security
python scripts/run_sast.py
python guardrails/compare.py
```
No extra pip command is needed. Continue with [Exercises](EXERCISES.md).

## Recovery
- Lost password: from `starter/`, with `.venv` activated, run
  `python manage.py changepassword alice`.
- Ollama connection error: from the root run `bash .devcontainer/start-ollama.sh`.
- Missing model: run `ollama pull qwen3:0.6b-q4_K_M`.
- Failed download/setup: from the root rerun `bash .devcontainer/setup.sh`.
  Existing secrets and passwords are preserved.
- CSRF error: open the normal forwarded HTTPS URL. Trusted origins for both ports
  are derived from the Codespaces environment.

Keep forwarded ports private. Never commit credentials, environments or databases.

## MCP credentials and NeMo
User consent creates a delegated access record and token. NeMo runs
in the application, not just in a separate comparison command. No service port
is exposed: MCP uses a private stdio process launched by Django.

For an existing checkout, rerun `python scripts/configure.py` from application after
installing its requirements in your already-selected Python 3.13 environment. This
preserves existing settings and passwords; it does not recreate the environment.
Before repairs use `python scripts/healthcheck.py`. After repairs use `python scripts/healthcheck.py --secured`. Use the exercise-specific checks while your repair is incomplete.

## Updating for ticket file uploads

In the existing activated environment, stop the website, run
`python manage.py migrate`, then use the startup command above. The migration
adds attachment metadata without replacing accounts or tickets. Imported ticket
files and attachment controls are described in
[Exercise 10](EXERCISES.md#10-fix-unsafe-ticket-imports-and-attachment-downloads).
Never submit the private `uploads/` folder.
