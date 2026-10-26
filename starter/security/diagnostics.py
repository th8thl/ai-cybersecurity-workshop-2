"""Redacted exception details for application logs and assistant Debug."""
from .redaction import sanitize

def failure_details(exc):
    """Keep diagnostic causes visible without exposing configured credentials."""
    causes, seen = [], set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        causes.append({"type": type(exc).__name__, "message": sanitize(str(exc))[:1500]})
        exc = exc.__cause__ or exc.__context__
    return causes

