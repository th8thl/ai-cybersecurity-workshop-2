"""Permissions chosen by the user on the assistant consent screen."""
from django import forms
from security.mcp_authorization import PERMISSIONS


class AssistantAuthorizationForm(forms.Form):
    permissions = forms.MultipleChoiceField(choices=list(PERMISSIONS.items()),
        widget=forms.CheckboxSelectMultiple, initial=['tickets:read'],
        label='Allow the assistant to', required=True)
    duration = forms.TypedChoiceField(choices=[(60,'1 minute'),(300,'5 minutes'),(1800,'30 minutes')],
        coerce=int, initial=1800, label='Access expires after')
