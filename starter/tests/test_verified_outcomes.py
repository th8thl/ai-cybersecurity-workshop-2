from .authorization_helpers import authorize_for_test
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from chatbot.ai_client import AIClientError
from chatbot.agent import run
from tickets.models import Ticket

@override_settings(MCP_TRANSPORT='inprocess-test', NEMO_CHECKS=False,
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class VerifiedOutcomeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('verified-outcome-user')
        self.ticket = Ticket.objects.create(owner=self.user, title='Registration help')
        self.client.force_login(self.user)
        authorize_for_test(self,self.user,self.client)

    def test_model_cannot_replace_success_with_a_service_error(self):
        proposals=iter([
            {'tool':'get_ticket','arguments':{'ticket_id':self.ticket.pk}},
            {'reply':'A required security service is unavailable.'}])
        result=run(self.user,'Read my ticket','qwen',[],planner=lambda *a,**k:next(proposals))
        self.assertEqual(result['reply'],f'Ticket #{self.ticket.pk}: Registration help. Its status is open.')
        self.assertEqual(next(item['proposal']['reply'] for item in result['trace'] if 'proposal' in item and 'reply' in item['proposal']), 'A required security service is unavailable.')

    @patch('chatbot.views.plan')
    def test_later_model_failure_does_not_hide_created_ticket(self, plan):
        plan.side_effect=[{'tool':'create_ticket','arguments':{'title':'New help request'}}, AIClientError('Model timed out')]
        response=self.client.post('/chatbot/',{'message':'I need help','provider':'qwen'},HTTP_ACCEPT='application/json')
        history=self.client.session['action_history']
        self.assertEqual(history[-2]['source'],'ticket')
        self.assertIn('New help request',history[-2]['text'])
        self.assertEqual(history[-1]['role'],'error')
        self.assertIn('Ticket result',response.json()['html'])
        self.assertIn('Application error',response.json()['html'])
        self.assertEqual(Ticket.objects.filter(owner=self.user,title='New help request').count(),1)
