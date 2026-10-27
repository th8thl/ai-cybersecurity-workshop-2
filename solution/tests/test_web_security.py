from django.conf import settings
from .common import TicketTestCase
from tickets.models import AuditEvent
from chatbot.tool_policy import execute
from django.test import Client

class SecurityTests(TicketTestCase):

    def test_audit_has_no_title_or_prompt(self):
        execute(self.alice, self.proposal())
        event = AuditEvent.objects.get()
        self.assertEqual(event.actor, self.alice)
        self.assertEqual(event.tool, 'get_ticket')
        self.assertFalse(hasattr(event, 'arguments'))

    def test_login_required(self):
        self.assertEqual(self.client.get('/chatbot/').status_code, 302)

    def test_authenticated_console_and_malformed_json(self):
        self.client.force_login(self.alice)
        self.assertContains(self.client.get('/chatbot/'), settings.CHATBOT_THEME['assistant_name'])
        response = self.client.post('/chatbot/', {'proposal': 'not json'})
        self.assertContains(response, 'Request rejected')

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.alice)
        self.assertEqual(client.post('/chatbot/', {'message': 'get ticket 1'}).status_code, 403)
