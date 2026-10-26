#!/usr/bin/env bash
set -euo pipefail
if ! command -v ollama >/dev/null 2>&1; then
  echo 'Ollama is missing. Rebuild the container to run setup.' >&2
  exit 1
fi
if ! curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  nohup ollama serve >/tmp/session2-ollama.log 2>&1 </dev/null &
fi
for attempt in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    exit 0
  fi
  sleep 1
done
cat /tmp/session2-ollama.log >&2
exit 1
