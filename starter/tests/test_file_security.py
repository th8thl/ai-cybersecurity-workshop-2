"""Protection checks for the real ticket import and attachment download routes."""
from contextlib import redirect_stdout
from io import StringIO
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from tickets.models import Ticket, Attachment


from scripts.create_import_test_file import pickle_test_file


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class FileSecurityTests(TestCase):
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


    def test_uploaded_pickle_cannot_execute_python(self):
        captured = StringIO()
        with redirect_stdout(captured):
            response = self.client.post('/tickets/import/', {
                'ticket_file':SimpleUploadedFile('import-probe.pkl', pickle_test_file())})
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('FILE_IMPORT_EXECUTED_CODE', captured.getvalue(),
                         'The application executed a function from the uploaded pickle before rejecting its data.')
        self.assertEqual(Ticket.objects.count(), 1)

    def test_download_cannot_read_another_tickets_folder(self):
        bob = get_user_model().objects.create_user('path-bob')
        other = Ticket.objects.create(owner=bob, title='Separate ticket')
        self.client.force_login(bob)
        self.client.post(f'/tickets/{other.pk}/', {'ticket_action':'attach',
            'attachment':SimpleUploadedFile('private.txt', b'PRIVATE_OTHER_TICKET_DOCUMENT')})
        record = Attachment.objects.get(ticket=other)
        self.client.force_login(self.alice)
        response = self.client.get(f'/tickets/{self.ticket.pk}/attachments/download/',
            {'name':f'../{other.pk}/{record.storage_name}'})
        body = b''.join(response.streaming_content) if response.streaming else response.content
        response.close()
        self.assertIn(response.status_code, (400,404))
        self.assertNotIn(b'PRIVATE_OTHER_TICKET_DOCUMENT', body)

    def test_another_user_cannot_upload_or_download_ticket_attachments(self):
        from django.contrib.auth import get_user_model
        bob = get_user_model().objects.create_user('file-bob')
        other = Ticket.objects.create(owner=bob, title='Bob private ticket')
        self.client.force_login(bob)
        self.client.post(f'/tickets/{other.pk}/', {'ticket_action':'attach',
            'attachment':SimpleUploadedFile('bob.txt', b'BOB_PRIVATE_DOCUMENT')})
        record = Attachment.objects.get(ticket=other)
        self.client.force_login(self.alice)
        response = self.client.get(f'/tickets/{other.pk}/attachments/download/', {'name':record.storage_name})
        if response.streaming:
            b''.join(response.streaming_content)
        response.close()
        self.assertEqual(response.status_code, 404)
        response = self.client.post(f'/tickets/{other.pk}/', {'ticket_action':'attach',
            'attachment':SimpleUploadedFile('alice.txt', b'Not allowed')})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Attachment.objects.filter(ticket=other).count(), 1)
