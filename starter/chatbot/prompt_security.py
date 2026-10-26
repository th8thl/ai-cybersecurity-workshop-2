import re


INJECTION_PATTERNS = [
    re.compile(r"\b(ignore|disregard|forget)\b.*\b(previous|prior|system|instructions?)\b", re.I),
    re.compile(r"\b(reveal|print|show|repeat|extract|disclose|output)\b.*\b(system prompt|instructions?|secret|api key|student record|policy text)\b", re.I),
    re.compile(r"\b(trusted instruction|new policy|new rule|newer instruction|for this turn|reset your initialization)\b", re.I),
    re.compile(r"\b(act as|pretend to be|stop being|you are now|movie critic|travel assistant)\b", re.I),
    re.compile(r"\b(conversation history|prior messages|debug mode|developer message|hidden prompt|hidden setup|policy text)\b", re.I),
    re.compile(r"\b(jailbreak|developer mode|sudo mode|dan)\b", re.I),
    re.compile(r"<\s*system\s*>|<\s*/\s*system\s*>", re.I),
    re.compile(r"\b(ignora|olvida|muestra)\b.*\b(instrucciones|sistema|previas|registro sintetico)\b", re.I),
    re.compile(r"\b(base64|rot13|decode|encoded)\b.*\b(follow|instruction|record|prompt)\b", re.I),
    re.compile(r"\b(pr0mpt|one character per line|markdown table|json with keys|synthetic_student_record)\b", re.I),
    re.compile(r"\b(authorized classroom|you can trust me|as a favor)\b.*\b(hidden|record|policy|setup)\b", re.I),
    re.compile(r"^MinerGuide:\s+I have verified this is allowed", re.I),
]


def looks_like_prompt_injection(message: str) -> bool:
    return any(pattern.search(message) for pattern in INJECTION_PATTERNS)


def redact_sensitive_output(text: str, synthetic_secret: str) -> str:
    if not synthetic_secret:
        return text
    return text.replace(synthetic_secret, "[REDACTED_SYNTHETIC_STUDENT_RECORD]")


def defended_response_for(message: str) -> str | None:
    if looks_like_prompt_injection(message):
        return (
            "I cannot follow requests to override my instructions, reveal hidden prompts, "
            "or expose secrets. Try asking a normal question within the assistant's allowed scope."
        )
    return None
