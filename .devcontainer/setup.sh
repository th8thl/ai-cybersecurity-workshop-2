#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo '=== Preparing starter: your workshop code ==='
python -m venv starter/.venv
starter/.venv/bin/python -m pip install -r starter/requirements.txt
(
  cd starter
  .venv/bin/python scripts/configure.py
  .venv/bin/python manage.py migrate
)
echo '=== Installing Ollama ==='
if ! command -v ollama >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y zstd
  curl -fsSL https://ollama.com/install.sh -o /tmp/session2-install-ollama.sh
  sh /tmp/session2-install-ollama.sh
fi
bash .devcontainer/start-ollama.sh
echo '=== Downloading workshop Qwen model ==='
ollama pull qwen3:0.6b-q4_K_M
echo '=== Demo login accounts: save new passwords below ==='
(
  cd starter
  .venv/bin/python manage.py seed_demo
)
echo 'Setup-generated demo passwords are printed above and saved locally in starter/.env.'
echo 'Show them again: cd starter && source .venv/bin/activate && python manage.py seed_demo --show-passwords'
echo 'These messages are in the Codespaces creation/setup output; runserver does not print passwords.'
echo '=== Setup complete ==='
echo 'Start: cd starter && source .venv/bin/activate && python manage.py runserver 0.0.0.0:8000'
