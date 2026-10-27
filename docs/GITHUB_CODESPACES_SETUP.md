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

The final **Demo login accounts** section of the Codespaces creation/setup output
prints setup-generated Alice/Bob passwords. Codespaces also displays the saved
login summary on attach, and `python manage.py seed_demo --show-passwords` reprints
it in an activated terminal. Older accounts without saved setup passwords need
the explicit reset command in the recovery section below. Database password hashes
cannot be displayed as original passwords. Downloads
can take several minutes. Wait for **Setup complete**. Ollama starts automatically
on later Codespace restarts. Ports 8000/8001 are private; 11434 is not forwarded.

## 2. Validate Ollama

### Validate Ollama before starting the exercises

In a terminal, run:

```bash
ollama --version
ollama list
ollama run qwen3:0.6b-q4_K_M "Reply with one word: READY"
```

Check all three results:

1. `ollama --version` prints a version: the command is installed.
2. `ollama list` connects to the server and lists `qwen3:0.6b-q4_K_M`.
3. `ollama run` generates a reply. The wording need not match exactly; a connection
   error, missing-model error or empty response is not a successful check.

From `starter`, activate `.venv` in this terminal, then confirm the application's
model settings (this command prints only the model name and endpoint):

```bash
source .venv/bin/activate
python manage.py shell -c "from django.conf import settings; print(settings.QWEN_MODEL, settings.QWEN_API_URL)"
```

The default model is `qwen3:0.6b-q4_K_M` and the endpoint is
`http://localhost:11434/api/chat`. If you selected another model in `.env`, use
that exact tag in both `ollama list` and `ollama run`. Restart Django after
changing `.env`. Continue only when generation works and the settings agree.

From the repository root, recover a stopped server with
`bash .devcontainer/start-ollama.sh`; pull the model if it is missing. Then rerun
the checks. Port 11434 stays internal; do not forward it publicly.

## 3. Start the application
From the repository root:
```bash
cd starter
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```
Open port **8000** in the **Ports** panel and use `/tickets/` on that website. Sign in with username `alice` and the password printed after `alice password:`. Follow [Exercise 1](EXERCISES.md#1-create-tickets-for-alice-and-bob) for the complete login and first-ticket walkthrough. Start with **New ticket** on the ticket list. For chat exercises open **Assistant**, keep **Qwen · local AI** selected (the default).

## 4. Run tools and exercises
In a second terminal, `cd starter` and `source .venv/bin/activate`:
```bash
source .venv/bin/activate
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

### Activate the environment in every exercise terminal

From `starter`, run `source .venv/bin/activate` in the Codespaces terminal. Then use `python ...` for
all workshop commands. Repeat activation in every new terminal.
See [exercise terminal instructions](EXERCISES.md#every-new-terminal-needs-the-workshop-environment).

## Demo passwords and terminal names

Setup saves only its generated Alice/Bob demo passwords in the local ignored
`starter/.env`. Codespaces prints the saved login summary on attach. In the
**Tests** terminal, activate `.venv`, then run `python manage.py seed_demo --show-passwords`
to display those logins again without changing accounts or tickets.
For an older workshop copy whose passwords were never saved, explicitly run
`python manage.py seed_demo --reset-passwords` once. This changes the Alice/Bob
demo passwords and prints the new ones. After that, `--show-passwords` reprints
them without changing accounts. Setup never silently resets existing passwords.

In Codespaces right-click each terminal tab and choose **Rename**: use **Website**
for Django, **Tests** for commands, and **NeMo** for Exercise 8's worker. Activate
the environment in each terminal. The starter starts with `NEMO_ENABLED=False`;
Exercise 8 sets it to `True`. Keep `NEMO_POLICY_MODE=deterministic` for Exercises
8–9 so the new content flow, rather than the semantic classifier, explains the result.
