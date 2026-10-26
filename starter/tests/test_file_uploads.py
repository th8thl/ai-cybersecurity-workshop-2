"""Real HTTP file uploads and downloads, using isolated files and records."""
import json
import tempfile
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from tickets.models import Ticket, Attachment


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class TicketFileTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='ticket-file-tests-')
        self.addCleanup(self.directory.cleanup)
        self.enterContext(override_settings(MEDIA_ROOT=self.directory.name))
        self.alice = get_user_model().objects.create_user('file-alice')
        self.ticket = Ticket.objects.create(owner=self.alice, title='Advising support')
        self.client.force_login(self.alice)

    def upload(self, contents=b'Enrollment document', name='enrollment.txt'):
        return self.client.post(f'/tickets/{self.ticket.pk}/', {
            'ticket_action':'attach', 'attachment':SimpleUploadedFile(name, contents)})

    @patch('chatbot.tool_policy.call', side_effect=AssertionError('File features must not call MCP'))
    @patch('chatbot.views.plan', side_effect=AssertionError('File features must not call a model'))
    def test_json_import_creates_ticket_owned_by_current_user(self, planner, mcp):
        response = self.client.post('/tickets/import/', {'ticket_file':SimpleUploadedFile(
            'request.json', b'{"title":"Imported registration request"}', content_type='application/json')})
        ticket = Ticket.objects.get(title='Imported registration request')
        self.assertEqual(ticket.owner, self.alice)
        self.assertEqual(ticket.status, 'open')
        self.assertRedirects(response, f'/tickets/{ticket.pk}/')
        planner.assert_not_called(); mcp.assert_not_called()

    def test_exported_ticket_can_be_imported(self):
        exported = self.client.get(f'/tickets/{self.ticket.pk}/export/')
        self.assertEqual(exported.json(), {'title':'Advising support'})
        self.assertIn('attachment;', exported['Content-Disposition'])
        response = self.client.post('/tickets/import/', {'ticket_file':SimpleUploadedFile('saved.json', exported.content)})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Ticket.objects.filter(owner=self.alice, title='Advising support').count(), 2)

    def test_downloadable_import_template_has_expected_fields(self):
        response = self.client.get('/tickets/import/template/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), {'title'})

    def test_attachment_upload_and_authenticated_download(self):
        self.assertEqual(self.upload().status_code, 302)
        attachment = Attachment.objects.get(ticket=self.ticket)
        self.assertEqual(attachment.original_name, 'enrollment.txt')
        self.assertEqual(attachment.uploaded_by, self.alice)
        page = self.client.get(f'/tickets/{self.ticket.pk}/')
        self.assertContains(page, 'Download enrollment.txt')
        response = self.client.get(f'/tickets/{self.ticket.pk}/attachments/download/', {'name':attachment.storage_name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'Enrollment document')
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        response.close()

    def test_missing_or_disallowed_attachment_is_reported(self):
        response = self.upload(name='script.html')
        self.assertContains(response, 'Choose a PDF, TXT, PNG or JPEG file.')
        self.assertFalse(Attachment.objects.exists())

    @override_settings(TICKET_MAX_ATTACHMENT_BYTES=4)
    def test_oversized_attachment_is_rejected(self):
        self.assertContains(self.upload(), 'The attachment is too large.')
        self.assertFalse(Attachment.objects.exists())

    @override_settings(TICKET_MAX_IMPORT_BYTES=4)
    def test_oversized_import_is_rejected(self):
        response = self.client.post('/tickets/import/', {'ticket_file':SimpleUploadedFile('large.json', b'{"title":"Too large"}')})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Ticket.objects.count(), 1)

    def test_import_rejects_owner_and_extra_fields(self):
        response = self.client.post('/tickets/import/', {'ticket_file':SimpleUploadedFile('request.json', b'{"title":"x","owner":123}')})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Ticket.objects.count(), 1)

    def test_invalid_json_reports_error_without_creating_ticket(self):
        response = self.client.post('/tickets/import/', {'ticket_file':SimpleUploadedFile('bad.json', b'not json')})
        self.assertContains(response, 'not valid JSON', status_code=400)
        self.assertEqual(Ticket.objects.count(), 1)

    def test_uploads_require_csrf_and_login(self):
        anonymous = self.client_class()
        self.assertEqual(anonymous.get('/tickets/import/').status_code, 302)
        self.assertEqual(anonymous.get(f'/tickets/{self.ticket.pk}/export/').status_code, 302)
        self.assertEqual(anonymous.get(f'/tickets/{self.ticket.pk}/attachments/download/').status_code, 302)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.alice)
        self.assertEqual(strict.post('/tickets/import/', {'ticket_file':SimpleUploadedFile('ticket.json', b'{"title":"x"}')}).status_code, 403)
        self.assertEqual(strict.post(f'/tickets/{self.ticket.pk}/', {'ticket_action':'attach','attachment':SimpleUploadedFile('x.txt', b'x')}).status_code, 403)
