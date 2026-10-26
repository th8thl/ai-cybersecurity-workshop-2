# NeMo checks used by the assistant

The application starts `worker.py` as a local Python process when the assistant
needs a NeMo check. `runtime.py` sends one JSON line through standard input and
reads the decision from standard output. The model does not call this process.
Checks run on messages, requested tools, tool results and final responses.
Ticket ownership remains the responsibility of the shared ticket service.

## Run the process yourself

From the folder containing `manage.py`, with its existing environment activated:

```text
python guardrails/worker.py
```

Follow [Exercise 8](../../docs/EXERCISES.md#8-run-nemo-directly-from-the-terminal)
for both request lines, expected responses, startup steps and shutdown keys.
Deterministic mode uses the programmed rules without Qwen. Semantic checks
add a separate request to local Qwen; the assistant's reply is a different call.

## Configure another rule

`policy.py` contains Python checks, `runtime.co` defines the NeMo steps, and
`runtime.yml` enables them. Follow
[Exercise 9](../../docs/EXERCISES.md#9-configure-a-new-nemo-rule).

## Run the automated comparisons

```text
python guardrails/compare.py
python guardrails/compare.py --configured
```

Use `--configured` after completing the new rule. `--semantic` additionally
requires Qwen running in Ollama. On the assistant page, turn on Debug and inspect
**Request trace · NeMo and MCP** to see decisions from the application process.
