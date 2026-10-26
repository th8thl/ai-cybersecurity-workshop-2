from django import forms

class TicketForm(forms.Form):
    title = forms.CharField(label="Request summary",max_length=120,strip=True,
        help_text="Describe what you need help with in 120 characters or fewer.",
        widget=forms.TextInput(attrs={"autofocus":True}))


class TicketImportForm(forms.Form):
    ticket_file = forms.FileField(label='Ticket file', widget=forms.ClearableFileInput(attrs={'accept':'.json'}),
        help_text='Maximum 64 KB. The file must contain a title, not an owner or ticket number.')

    def clean_ticket_file(self):
        from django.conf import settings
        upload = self.cleaned_data['ticket_file']
        if upload.size > settings.TICKET_MAX_IMPORT_BYTES:
            raise forms.ValidationError('The ticket file is too large. Choose a file no larger than 64 KB.')
        return upload


class AttachmentForm(forms.Form):
    attachment = forms.FileField(label='Attach a document or image',
        help_text='PDF, TXT, PNG or JPEG; maximum 2 MB.')

    def clean_attachment(self):
        from django.conf import settings
        from pathlib import Path
        upload = self.cleaned_data['attachment']
        if upload.size > settings.TICKET_MAX_ATTACHMENT_BYTES:
            raise forms.ValidationError('The attachment is too large. Choose a file no larger than 2 MB.')
        if Path(upload.name).suffix.lower() not in {'.pdf', '.txt', '.png', '.jpg', '.jpeg'}:
            raise forms.ValidationError('Choose a PDF, TXT, PNG or JPEG file.')
        return upload
