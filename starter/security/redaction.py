import re
import os
from django.conf import settings
from .mcp_authorization import current_access_token

def sanitize(value):
    if isinstance(value, dict):
        return {sanitize(str(k)):sanitize(v) for k,v in value.items()}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    if not isinstance(value, str):
        return value
    known = [settings.SECRET_KEY, settings.GEMINI_API_KEY, os.getenv("DEMO_ALICE_PASSWORD"), os.getenv("DEMO_BOB_PASSWORD")]
    known.append(current_access_token())
    for secret in known:
        if secret:
            value = value.replace(secret, '[REDACTED]')
    return re.sub(r'(?:mcp_[A-Za-z0-9_-]{32,}|AIza[0-9A-Za-z_-]{30,}|sk-[A-Za-z0-9_-]{24,})', '[REDACTED]', value)
