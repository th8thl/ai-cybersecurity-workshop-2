"""Run NeMo checks in a private worker. It loads policy.py, runtime.co and runtime.yml at startup; restart the application after configuration edits."""
import atexit
import json
import os
import queue
import subprocess
import sys
import threading
from django.conf import settings

class GuardrailBlocked(PermissionError):
    pass

_lock = threading.Lock()
_worker = None
_responses = None

def close_worker():
    global _worker
    if _worker is not None:
        _worker.terminate()
        try:
            _worker.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _worker.kill()
        _worker = None

atexit.register(close_worker)

def _start():
    global _worker, _responses
    env = {key:value for key,value in os.environ.items()
        if key.upper() in {"SYSTEMROOT","WINDIR","PATH","TEMP","TMP","HOME","USERPROFILE"}}
    env.update(NEMO_QWEN_URL=settings.QWEN_API_URL, NEMO_QWEN_MODEL=settings.QWEN_MODEL,
               PYTHONUNBUFFERED="1")
    _worker = subprocess.Popen([sys.executable,str(settings.BASE_DIR/'guardrails/worker.py')],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
        text=True,encoding="utf-8",env=env,cwd=settings.BASE_DIR/'guardrails')
    _responses = queue.Queue()
    process, responses = _worker, _responses
    def collect():
        for line in process.stdout:
            responses.put(line)
        responses.put(None)
    threading.Thread(target=collect,daemon=True).start()

def check(stage, payload, provider="mock", trace=None):
    if not getattr(settings,"NEMO_CHECKS",True):
        if trace is not None:
            trace.append({"stage":stage, "engine":"NeMo Guardrails", "mode":"disabled", "skipped":True})
        return  # Explicit workshop state; authorization checks remain active.
    mode = "deterministic" if provider == "mock" else getattr(settings,"NEMO_POLICY_MODE","semantic")
    if mode not in {"deterministic","semantic"}:
        raise GuardrailBlocked("Unknown NeMo policy mode; refusing action.")
    with _lock:
        global _worker
        try:
            if _worker is None or _worker.poll() is not None:
                _start()
            _worker.stdin.write(json.dumps({"stage":stage,"payload":payload,"mode":mode})+'\n')
            _worker.stdin.flush()
            line = _responses.get(timeout=75)
            if line is None:
                raise RuntimeError("NeMo worker exited.")
            verdict = json.loads(line)
        except Exception as exc:
            close_worker()
            raise GuardrailBlocked("NeMo is unavailable; no tool action was authorized.") from exc
    if trace is not None:
        trace.append(verdict)
    if not verdict.get("allowed"):
        raise GuardrailBlocked("NeMo blocked this request at the " + stage + " boundary.")
