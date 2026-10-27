# Set up the workshop in Codespaces

Use [Codespaces setup](GITHUB_CODESPACES_SETUP.md), then complete its Ollama
validation checks before Exercise 1. Work in `starter`; `solution` is the answer key.

## Terminal names and activation

Right-click a terminal tab → **Rename**. Use **Website** for Django, **Tests**
for commands, and **NeMo** for Exercise 8's worker. Activate each new terminal:

```bash
cd starter
source .venv/bin/activate
```

Skip `cd starter` if already there. Start Django in Website:

```bash
python manage.py runserver 0.0.0.0:8000
```

Open port **8000** in the **Ports** panel and visit `/tickets/` on its forwarded
website. Keep Website running while using Tests for commands.

## Demo logins

In Tests, after activation:

```bash
python manage.py seed_demo --show-passwords
```

For old demo accounts whose passwords were never saved, explicitly run
`python manage.py seed_demo --reset-passwords` once to generate and print new
Alice/Bob passwords. Later, `--show-passwords` displays them without changing them.

## Exercises and returning later

Follow [the exercises](EXERCISES.md). Qwen is the default. The starter begins with
NeMo off; Exercise 8 enables it, and Exercise 9 adds the deterministic content flow.
On later days, activate the existing environment and start Django again; do not
recreate it. Follow [Ollama validation](GITHUB_CODESPACES_SETUP.md#2-validate-ollama)
if the model server is unavailable. Assistant grants can expire independently of
website sign-in; renew them through **Authorization** when prompted.
