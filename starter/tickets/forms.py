from django import forms

class TicketForm(forms.Form):
    title = forms.CharField(label="Request summary",max_length=120,strip=True,
        help_text="Describe what you need help with in 120 characters or fewer.",
        widget=forms.TextInput(attrs={"autofocus":True}))
