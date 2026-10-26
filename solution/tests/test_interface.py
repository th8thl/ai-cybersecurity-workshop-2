from .authorization_helpers import authorize_for_test
from unittest.mock import patch
from django.test import override_settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from tickets.models import Ticket, Approval


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
@override_settings(MCP_TRANSPORT="inprocess-test", NEMO_CHECKS=False)
class InterfaceTests(TestCase):
    def setUp(self):
        self.alice = get_user_model().objects.create_user('alice', password='test-only')
        self.bob = get_user_model().objects.create_user('bob', password='test-only')
        self.ticket = Ticket.objects.create(owner=self.alice, title='Advising appointment')
        self.client.force_login(self.alice)
        authorize_for_test(self,self.alice,self.client)

    def test_tickets_are_links_and_open_details(self):
        response = self.client.get('/chatbot/')
        self.assertContains(response, f'href="/tickets/{self.ticket.pk}/"')
        self.assertContains(self.client.get(f'/tickets/{self.ticket.pk}/'), 'Advising appointment')

    def test_main_chat_does_not_ask_for_json(self):
        response = self.client.get('/chatbot/')
        self.assertContains(response, 'Send message')
        self.assertContains(response, 'id="debug-toggle"')
        content = response.content.decode()
        self.assertNotIn('name="proposal"', content.split('id="debug-panel"')[0])

    def test_natural_language_creates_ticket_and_conversation_persists(self):
        self.client.post('/chatbot/', {'message':'I need help with registration', 'provider':'mock'})
        self.assertTrue(Ticket.objects.filter(owner=self.alice, title='Help with registration').exists())
        response = self.client.get('/chatbot/')
        self.assertContains(response, 'I need help with registration')
        self.assertContains(response, "I&#x27;ve created ticket")

    def test_other_users_ticket_details_are_denied(self):
        ticket = Ticket.objects.create(owner=self.bob, title='Bob private request')
        response = self.client.get(f'/tickets/{ticket.pk}/')
        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, 'Bob private request', status_code=404)

    def test_ticket_button_requests_confirmation_and_cancel_keeps_open(self):
        response = self.client.post('/chatbot/', {'ticket_action':'close','ticket_id':self.ticket.pk})
        self.assertContains(response, 'Review it on the ticket page')
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, 'open')
        approval = Approval.objects.get(actor=self.alice)
        response = self.client.post(f'/tickets/{self.ticket.pk}/', {'ticket_action':'cancel','approval_id':str(approval.pk)}, follow=True)
        self.assertContains(response, 'Cancelled. Your ticket will stay open.')
        approval.refresh_from_db()
        self.assertTrue(approval.consumed)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, 'open')

    def test_approval_cancellation_is_bound_to_user(self):
        approval = Approval.objects.create(actor=self.bob, ticket=self.ticket)
        self.client.post(f'/tickets/{self.ticket.pk}/', {'ticket_action':'cancel','approval_id':str(approval.pk)})
        approval.refresh_from_db()
        self.assertFalse(approval.consumed)

    def test_greeting_does_not_create_ticket(self):
        self.client.post('/chatbot/', {'message':'Hello', 'provider':'mock'})
        self.assertEqual(Ticket.objects.count(), 1)

    def test_repeated_form_submission_does_not_create_duplicate_ticket(self):
        page = self.client.get('/chatbot/')
        token = page.context['form_token']
        payload = {'message':'I need help with registration', 'provider':'mock', 'form_token':token}
        self.client.post('/chatbot/', payload)
        self.client.post('/chatbot/', payload)
        self.assertEqual(Ticket.objects.filter(title='Help with registration').count(), 1)

@override_settings(MCP_TRANSPORT='inprocess-test',NEMO_CHECKS=False,
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DirectTicketApprovalTests(TestCase):
    def setUp(self):
        self.alice=get_user_model().objects.create_user('direct-approval-alice')
        self.ticket=Ticket.objects.create(owner=self.alice,title='Direct ticket workflow')
        self.client.force_login(self.alice)

    @override_settings(NEMO_CHECKS=True, MCP_TRANSPORT='mcp')
    @patch('chatbot.tool_policy.call', side_effect=RuntimeError('MCP unavailable'))
    def test_close_cancel_and_confirm_without_chat(self, mcp):
        url=f'/tickets/{self.ticket.pk}/'
        self.client.post(url,{'ticket_action':'close'})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status,'open')
        approval=Approval.objects.get(actor=self.alice,consumed=False)
        self.assertContains(self.client.get(url),'Yes, close ticket')
        self.client.post(url,{'ticket_action':'cancel','approval_id':str(approval.pk)})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status,'open')
        self.client.post(url,{'ticket_action':'close'})
        approval=Approval.objects.get(actor=self.alice,consumed=False)
        self.client.post(url,{'ticket_action':'confirm','approval_id':str(approval.pk)})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status,'closed')
        self.assertNotIn('action_history',self.client.session)
        mcp.assert_not_called()

    def test_confirmation_cannot_be_submitted_on_another_ticket(self):
        other=Ticket.objects.create(owner=self.alice,title='Another own ticket')
        approval=Approval.objects.create(actor=self.alice,ticket=other)
        self.client.post(f'/tickets/{self.ticket.pk}/',{'ticket_action':'confirm','approval_id':str(approval.pk)})
        other.refresh_from_db()
        self.assertEqual(other.status,'open')
        approval.refresh_from_db()
        self.assertFalse(approval.consumed)

