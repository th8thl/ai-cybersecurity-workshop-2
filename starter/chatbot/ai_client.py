from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from urllib import error, request

from django.conf import settings


class AIClientError(Exception):
    """Raised when the configured model provider cannot return a response."""


def theme():
    return settings.CHATBOT_THEME


PROMPTS_DIR = Path(settings.BASE_DIR) / "prompts"


def _prompt_template(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").strip()


def _prompt_context(**overrides: str) -> dict[str, str]:
    active_theme = theme()
    context = {
        "assistant_name": active_theme["assistant_name"],
        "assistant_role": active_theme["assistant_role"],
        "audience": active_theme["audience"],
        "synthetic_secret_label": active_theme["synthetic_secret_label"],
        "synthetic_secret_label_lower": active_theme["synthetic_secret_label"].lower(),
        "synthetic_secret": settings.SYNTHETIC_SECRET,
        "allowed_scope": active_theme["allowed_scope"],
        "redirect_topic": active_theme["redirect_topic"],
    }
    context.update(overrides)
    return context


def render_prompt(name: str, **context: str) -> str:
    return _prompt_template(name).format(**context)


def system_policy() -> str:
    return render_prompt("system_policy.txt", **_prompt_context())


def model_prompt(user_message: str, history: list[dict[str, str]]) -> str:
    transcript = "\n".join(f"{item['role']}: {item['content']}" for item in history[-3:])
    return render_prompt(
        "request.txt",
        **_prompt_context(
            system_policy=system_policy(),
            transcript=transcript,
            user_message=user_message,
        ),
    )


@dataclass
class ChatResult:
    text: str
    provider: str
    model: str | None = None
    attempts: list[dict[str, str | float]] | None = None
    prompt: str | None = None


class MockChatClient:
    """Deterministic local model used when no Gemini API key is configured."""

    provider = "local-mock"

    def complete(self, user_message: str, history: list[dict[str, str]]) -> ChatResult:
        active_theme = theme()
        mock_responses = active_theme["mock_responses"]
        prompt = model_prompt(user_message, history)
        lower = user_message.lower()
        if "synthetic student record" in lower or "student record" in lower:
            text = settings.SYNTHETIC_SECRET
        elif "secret" in lower or "system prompt" in lower or "instructions" in lower:
            text = (
                "Because this starter app is intentionally vulnerable, here is lab-only data: "
                f"{settings.SYNTHETIC_SECRET}. The hidden policy says: {system_policy().strip()}"
            )
        elif "hello" in lower or "hi" in lower:
            text = mock_responses["greeting"]
        elif any(keyword in lower for keyword in active_theme.get("topic_keywords", [])):
            text = mock_responses["topic"]
        elif any(keyword in lower for keyword in ["poem", "recipe", "pirate", "travel", "vacation", "movie critic"]):
            text = mock_responses["off_topic"]
        else:
            text = mock_responses["default"]
        return ChatResult(text=text, provider=self.provider, model=None, attempts=[], prompt=prompt)


class GeminiChatClient:
    provider = "gemini"

    def __init__(self):
        from google import genai

        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def complete(self, user_message: str, history: list[dict[str, str]]) -> ChatResult:
        prompt = model_prompt(user_message, history)
        attempts = []
        models = [settings.GEMINI_MODEL]
        models.extend(model for model in settings.GEMINI_FALLBACK_MODELS if model not in models)

        for model in models:
            started_at = perf_counter()
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                attempts.append(
                    {
                        "model": model,
                        "status": "ok",
                        "duration_ms": round((perf_counter() - started_at) * 1000, 1),
                    }
                )
                return ChatResult(
                    text=response.text or "",
                    provider=self.provider,
                    model=model,
                    attempts=attempts,
                    prompt=prompt,
                )
            except Exception as exc:
                attempts.append(
                    {
                        "model": model,
                        "status": "error",
                        "duration_ms": round((perf_counter() - started_at) * 1000, 1),
                        "error": str(exc),
                    }
                )
                if "503" not in str(exc) and "UNAVAILABLE" not in str(exc):
                    break

        raise AIClientError(
            "Gemini request failed for all configured models. "
            f"Tried: {', '.join(models)}. Provider errors: "
            + " | ".join(f"{item['model']}: {item.get('error', '')}" for item in attempts)
        )


class QwenChatClient:
    provider = "qwen"

    def complete(self, user_message: str, history: list[dict[str, str]]) -> ChatResult:
        prompt = model_prompt(user_message, history)
        started_at = perf_counter()
        payload = {
            "model": settings.QWEN_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "think": False,
            "stream": False,
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            settings.QWEN_API_URL,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=120) as response:
                raw = response.read().decode("utf-8")
            data = json.loads(raw)
            message = data.get("message", {})
            text = message.get("content", "")
            return ChatResult(
                text=text,
                provider=self.provider,
                model=settings.QWEN_MODEL,
                attempts=[
                    {
                        "model": settings.QWEN_MODEL,
                        "status": "ok",
                        "duration_ms": round((perf_counter() - started_at) * 1000, 1),
                    }
                ],
                prompt=prompt,
            )
        except (OSError, error.URLError, json.JSONDecodeError) as exc:
            raise AIClientError(f"Qwen request failed: {exc}") from exc


def get_chat_client(provider: str | None = None):
    selected_provider = (provider or settings.AI_PROVIDER or "mock").lower()
    if selected_provider == "gemini":
        if not settings.GEMINI_API_KEY or not settings.GEMINI_MODEL:
            raise AIClientError("Set GEMINI_API_KEY and GEMINI_MODEL in .env before selecting Gemini.")
        return GeminiChatClient()
    if selected_provider == "qwen":
        return QwenChatClient()
    return MockChatClient()



