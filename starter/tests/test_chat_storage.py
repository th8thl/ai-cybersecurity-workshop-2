from .authorization_helpers import authorize_for_test
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from unittest.mock import patch
from tickets.models import Ticket

@override_settings(MCP_TRANSPORT='inprocess-test', NEMO_CHECKS=False,
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ChatInteractionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('alice', password='test-only')
        self.client.force_login(self.user)
        authorize_for_test(self,self.user,self.client)

    def post(self, **data):
        return self.client.post('/chatbot/', data, HTTP_ACCEPT='application/json')

    def test_async_creation_refreshes_tickets_and_persists_conversation(self):
        response = self.post(message='I need help with registration', provider='mock', form_token='first')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIsNone(payload['error'])
        self.assertIn('Help with registration', payload['html'])
        self.assertEqual(Ticket.objects.get().owner, self.user)
        self.assertEqual(len(self.client.session['action_history']), 2)
        self.assertContains(self.client.get('/chatbot/'), 'I need help with registration')
        self.assertIn('does not send a model prompt', payload['prompts'])

    def test_async_duplicate_submission_does_not_repeat_write(self):
        self.post(message='I need help with registration', provider='mock', form_token='once')
        self.post(message='I need help with registration', provider='mock', form_token='once')
        self.assertEqual(Ticket.objects.count(), 1)

    @patch('chatbot.views.plan')
    def test_actual_model_prompts_appear_in_debug(self, plan):
        def record(message, provider, context=None, debug=None):
            debug.append({'system':'Exact model instructions', 'user':message})
            return {'reply':'Hello Alice'}
        plan.side_effect = record
        payload = self.post(message='Hello', provider='qwen').json()
        self.assertIn('Exact model instructions', payload['prompts'])
        self.assertIn('Hello Alice', payload['html'])

    def test_csrf_still_applies_to_async_requests(self):
        client=Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post('/chatbot/', {'message':'Hello'}, HTTP_ACCEPT='application/json').status_code,403)

    def test_only_one_chat_interface_is_exposed(self):
        self.assertEqual(self.client.get('/actions/').status_code,404)
        self.assertEqual(self.client.get('/session1/').status_code,404)
        self.assertEqual(self.client.get('/chat/').status_code,404)
        self.assertContains(self.client.get('/chatbot/'),'id="debug-toggle"')
