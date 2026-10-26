from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from tickets.models import Ticket

@override_settings(MCP_TRANSPORT='inprocess-test',NEMO_CHECKS=False,
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class TicketPortalTests(TestCase):
    def setUp(self):
        self.alice=get_user_model().objects.create_user('portal-alice')
        self.bob=get_user_model().objects.create_user('portal-bob')
        self.own=Ticket.objects.create(owner=self.alice,title='My advising request')
        Ticket.objects.create(owner=self.bob,title='Private Bob request')
        self.client.force_login(self.alice)

    def test_home_and_login_land_on_tickets(self):
        from django.conf import settings
        self.assertRedirects(self.client.get('/'),'/tickets/')
        self.assertEqual(settings.LOGIN_REDIRECT_URL,'/tickets/')

    def test_dashboard_lists_only_current_users_tickets(self):
        response=self.client.get('/tickets/')
        self.assertContains(response,'My advising request')
        self.assertNotContains(response,'Private Bob request')
        self.assertContains(response,'href="/tickets/new/"')
        self.assertContains(response,'href="/chatbot/"')

    @patch('chatbot.views.plan',side_effect=AssertionError('Ticket forms must not call a model'))
    def test_create_and_read_ticket_without_chat(self, planner):
        response=self.client.post('/tickets/new/',{'title':'Registration problem'})
        ticket=Ticket.objects.get(owner=self.alice,title='Registration problem')
        self.assertRedirects(response,f'/tickets/{ticket.pk}/')
        self.assertContains(self.client.get(response.url),'Registration problem')
        self.assertNotIn('action_history',self.client.session)
        planner.assert_not_called()

    def test_create_form_rejects_blank_summary(self):
        response=self.client.post('/tickets/new/',{'title':'   '})
        self.assertContains(response,'This field is required.')
        self.assertEqual(Ticket.objects.filter(owner=self.alice).count(),1)

    def test_nested_chat_ticket_route_is_removed(self):
        self.assertEqual(self.client.get(f'/chatbot/tickets/{self.own.pk}/').status_code,404)

    def test_ticket_writes_require_csrf(self):
        client=Client(enforce_csrf_checks=True)
        client.force_login(self.alice)
        self.assertEqual(client.post('/tickets/new/',{'title':'No CSRF'}).status_code,403)
        self.assertEqual(client.post(f'/tickets/{self.own.pk}/',{'ticket_action':'close'}).status_code,403)

    @override_settings(NEMO_CHECKS=True, MCP_TRANSPORT='mcp')
    @patch('chatbot.views.authorization_status', side_effect=AssertionError('Ticket pages must not inspect assistant authorization'))
    @patch('chatbot.tool_policy.call', side_effect=RuntimeError('MCP unavailable'))
    @patch('chatbot.views.check', side_effect=RuntimeError('NeMo unavailable'))
    @patch('chatbot.views.plan', side_effect=RuntimeError('Model unavailable'))
    def test_ticket_pages_work_without_assistant_services(self, planner, nemo, mcp, setup):
        self.assertEqual(self.client.get('/tickets/').status_code, 200)
        response = self.client.post('/tickets/new/', {'title':'Independent ticket'})
        ticket = Ticket.objects.get(owner=self.alice, title='Independent ticket')
        self.assertRedirects(response, f'/tickets/{ticket.pk}/')
        self.assertContains(self.client.get(response.url), 'Independent ticket')
        for dependency in (planner, nemo, mcp, setup):
            dependency.assert_not_called()
