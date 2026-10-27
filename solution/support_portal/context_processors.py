from django.conf import settings
from .theme import portal_theme


def workshop_theme(request):
    return {"theme": settings.CHATBOT_THEME, "portal": portal_theme()}
