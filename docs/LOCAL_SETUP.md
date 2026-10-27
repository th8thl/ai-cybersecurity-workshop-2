# Local setup — Session 2

Use Python **3.12 or 3.13**. All steps below are for your working code in
`starter/`. Leave `solution/` alone; it is the completed answer key.

## 1. Check Python before first-time setup

NeMo does **not** support Python 3.14. On Windows, run:
```powershell
py -3.13 --version
```
It must report Python 3.13.x. If unavailable, install Python 3.13 before continuing.
The commands below select 3.13 explicitly, regardless of the default `python`.

If `.venv` already exists, activate it with `.\.venv\Scripts\Activate.ps1`, then run `python --version` first.
If it reports 3.14, stop: the setup commands below are for a new environment.
They do not upgrade or convert an existing environment.

## Windows PowerShell: new environment
From the Session 2 repository root:
```powershell
cd starter
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```
If PowerShell blocks activation, use Command
Prompt and run `.venv\Scripts\activate.bat`, then use `python` for the remaining commands.

macOS/Linux, from the repository root:
```bash
cd starter
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```
Check `python3.13 --version` first; install Python 3.13 if unavailable. This installation
includes Django, model clients, schema validation, Bandit, Semgrep and NeMo.
No second Python environment or extra dependency installation is needed.

## 2. Configure and launch
The configure command prepares `.env`. Each user grants assistant access after
signing in through **Assistant → Authorize assistant**. See
[the permissions and token flow](MCP_AUTHORIZATION.md).

Still inside `starter/`, with `.venv` activated:
```
python scripts/configure.py
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```
Save the passwords printed after `alice password:` and `bob password:`. Open http://127.0.0.1:8000/tickets/. The username is `alice` (lowercase); use its printed password. On **Your tickets**, click **New ticket**, enter a **Request summary**, and click **Create ticket**. Expect the request detail page with **Open** status. Use **Assistant** in the navigation for the separate chat exercises. Follow [Exercise 1](EXERCISES.md#1-create-tickets-for-alice-and-bob) for the complete login and first-ticket walkthrough, including password recovery.

## 3. Prepare Ollama for Qwen and NeMo
Ollama is a separate system application; pip does not install it. Install it from
https://ollama.com/download and start it. On Linux use the official installer,
then `ollama serve` if it is not already running as a service. In another terminal:
```
ollama pull qwen3:0.6b-q4_K_M
ollama list
```
The list must contain `qwen3:0.6b-q4_K_M` (approximately 522 MB). Select **Qwen · local AI**
in the workshop console. `starter/.env` already points to this model at localhost:11434. The same
model serves the NeMo exercise.

### Validate Ollama before starting the exercises

In a terminal, run:

```text
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

```text
python manage.py shell -c "from django.conf import settings; print(settings.QWEN_MODEL, settings.QWEN_API_URL)"
```

The default model is `qwen3:0.6b-q4_K_M` and the endpoint is
`http://localhost:11434/api/chat`. If you selected another model in `.env`, use
that exact tag in both `ollama list` and `ollama run`. Restart Django after
changing `.env`. Continue only when generation works and the settings agree.

If the server cannot be reached, start the Ollama app or run `ollama serve` in a
separate terminal and keep it running. If the tag is missing, run
`ollama pull qwen3:0.6b-q4_K_M`, then repeat the checks.

## 4. Workshop tools
Open another terminal, return to `starter/`, and activate `.venv` again:
```
python manage.py test tests.test_ticket_portal
python manage.py test tests.test_chat_storage
python manage.py test tests.test_prompt_security
python scripts/run_sast.py
python guardrails/compare.py
```
The first command must pass. Scanner results go to `starter/results/`; findings
are review evidence. Only Qwen/semantic NeMo mode needs Ollama; Demo and the default NeMo comparison do not. Continue with [Exercises](EXERCISES.md),
including the intentionally failing action security contract. Do not weaken tests.

## Optional Gemini
Set GEMINI_API_KEY and GEMINI_MODEL in `starter/.env`, restart Django,
and select Gemini. Choose a model available to your account. No API key is needed
for mock/Qwen/NeMo. Never put real keys in source or prompts.

## MCP credentials and NeMo
User consent creates a delegated access record and token. NeMo runs
in the application, not just in a separate comparison command. No service port
is exposed: MCP uses a private stdio process launched by Django.

For an existing checkout, run `python manage.py migrate` once to add the
authorization table, then restart Django. Users grant access through the browser.
Before changing code, `python scripts/healthcheck.py` checks that the exercise reproduces the intended flaws. After completing repairs, use `python scripts/healthcheck.py --secured`. Follow the exercise checkpoints for partially repaired code.

### Activate the environment in every exercise terminal

From `starter`, run `.\.venv\Scripts\Activate.ps1` on Windows PowerShell or
`source .venv/bin/activate` in Codespaces/macOS/Linux. Then use `python ...` for
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
