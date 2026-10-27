"""Session 2 excludes the file features taught in Session 4."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from tickets.models import Ticket


class SessionScopeTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user('scope-user')
        self.ticket = Ticket.objects.create(owner=user, title='Ordinary ticket')
        self.client.force_login(user)

    def test_file_routes_are_absent(self):
        for path in ['/tickets/import/', '/tickets/import/template/',
                     f'/tickets/{self.ticket.pk}/export/',
                     f'/tickets/{self.ticket.pk}/attachments/download/']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_ticket_pages_have_no_file_controls(self):
        listing = self.client.get('/tickets/')
        detail = self.client.get(f'/tickets/{self.ticket.pk}/')
        self.assertContains(detail, 'Ordinary ticket')
        self.assertNotContains(listing, 'Import a ticket file')
        self.assertNotContains(detail, 'Upload attachment')
        self.assertNotContains(detail, 'Export ticket as JSON')
