#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -x starter/.venv/bin/python ] && [ -f starter/.env ]; then
  echo '=== Workshop demo logins (setup-generated; keep local) ==='
  (cd starter && .venv/bin/python manage.py seed_demo --show-passwords)
fi
