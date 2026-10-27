"""Theme-backed presentation and demo vocabulary for the ticket application."""
from django.conf import settings


def portal_theme():
    portal = {
        "title": "Support Tickets", "subtitle": "Create and manage support requests",
        "assistant_intro": "Open a support request or check an existing ticket.",
        "greeting": "Tell me what you need help with. I can create, read or request closure of a ticket.",
        "input_placeholder": "Describe your support request",
        "examples": [], "request_keywords": [],
        "fallback_reply": "Describe your support request, or select a ticket to view or close it.",
    }
    portal.update(settings.CHATBOT_THEME.get("ticket_portal", {}))
    return portal
