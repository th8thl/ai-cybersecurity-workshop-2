"""The same portal and planner must work with a non-campus theme."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from chatbot.planner import plan

ALT = json.loads((Path(settings.BASE_DIR) / 'themes/support_desk.json').read_text(encoding='utf-8'))


@override_settings(CHATBOT_THEME=ALT, MCP_TRANSPORT='inprocess-test', NEMO_CHECKS=False)
class ThemeIntegrationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('theme-user')
        self.client.force_login(self.user)

    def test_portal_login_and_assistant_use_selected_theme(self):
        self.assertContains(self.client.get('/tickets/'), 'Workplace Service Desk')
        response = self.client.get('/chatbot/')
        for expected in ['DeskGuide', 'my printer is offline', 'Printer help']:
            self.assertContains(response, expected)
        for forbidden in ['Campus Support', 'academic advising', 'MinerGuide', 'UTEP']:
            self.assertNotContains(response, forbidden)
        self.client.logout()
        self.assertContains(self.client.get('/accounts/login/'), 'Workplace Service Desk')

    def test_demo_vocabulary_comes_from_theme(self):
        proposal = plan('My printer is offline', 'mock')
        self.assertEqual(proposal['tool'], 'create_ticket')
        self.assertIn('printer', proposal['arguments']['title'])
        self.assertEqual(plan('hello', 'mock')['reply'], ALT['ticket_portal']['fallback_reply'])

    @patch('chatbot.planner.request.urlopen')
    def test_model_receives_selected_scope_and_structured_schema(self, urlopen):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({'message': {'content': json.dumps({'reply': 'How can I help?'})}}).encode()
        urlopen.return_value = response
        plan('Printer help', 'qwen')
        payload = json.loads(urlopen.call_args.args[0].data)
        prompt = payload['messages'][0]['content']
        self.assertIn(ALT['allowed_scope'], prompt)
        self.assertIn(ALT['assistant_role'], prompt)
        self.assertNotIn('campus', prompt.lower())
        self.assertNotIn('UTEP', prompt)
        self.assertIn('anyOf', payload['format'])
