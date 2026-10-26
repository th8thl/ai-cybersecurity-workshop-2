"""Private long-lived NeMo worker; stdout is a JSON line protocol, not a web API."""
import asyncio
import json
import os
import sys
from pathlib import Path
os.environ["NEMOGUARDRAILS_LLM_FRAMEWORK"] = "langchain"
from langchain_core.language_models.llms import LLM
from nemoguardrails import LLMRails, RailsConfig
from policy import deterministic, semantic, bulk_export_allowed

class NoGeneration(LLM):
    """Input-only rails never generate a conversation response."""
    @property
    def _llm_type(self):
        return "workshop-input-only"
    def _call(self, prompt, stop=None, run_manager=None, **kwargs):
        raise RuntimeError("Unexpected main-model generation in input-only rails.")
    async def _acall(self, prompt, stop=None, run_manager=None, **kwargs):
        return self._call(prompt, stop, run_manager, **kwargs)

async def check_workshop_policy(context=None):
    envelope = json.loads(context["user_message"])
    allowed = deterministic(envelope["stage"], envelope["payload"])
    if allowed and envelope["mode"] == "semantic":
        allowed = await asyncio.to_thread(semantic, envelope["stage"], envelope["payload"],
            os.environ["NEMO_QWEN_URL"], os.environ["NEMO_QWEN_MODEL"])
    return allowed

async def check_bulk_export_policy(context=None):
    envelope = json.loads(context["user_message"])
    return bulk_export_allowed(envelope["stage"], envelope["payload"])

async def main():
    directory = Path(__file__).resolve().parent
    os.chdir(directory)  # Never discover the application packages as NeMo code.
    config = RailsConfig.from_content(yaml_content=(directory/'runtime.yml').read_text(),
        colang_content=(directory/'runtime.co').read_text())
    rails = LLMRails(config, llm=NoGeneration())
    rails.register_action(check_workshop_policy, name="check_workshop_policy")
    rails.register_action(check_bulk_export_policy, name="check_bulk_export_policy")
    for line in sys.stdin:
        try:
            envelope = json.loads(line)
            result = await rails.generate_async(messages=[{"role":"user","content":json.dumps(envelope)}],
                options={"rails":["input"],"output_vars":True})
            blocked = bool((result.output_data or {}).get("triggered_input_rail"))
            print(json.dumps({"allowed":not blocked,"engine":"NeMo Guardrails", "stage":envelope["stage"],
                "mode":envelope["mode"],"active_flows":config.rails.input.flows}), flush=True)
        except Exception:
            print(json.dumps({"allowed":False,"engine":"NeMo Guardrails","error":"policy check failed"}), flush=True)

if __name__ == "__main__":
    asyncio.run(main())
