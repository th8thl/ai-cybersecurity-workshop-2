from .authorization_helpers import authorize_for_test
from unittest.mock import patch
from django.test import SimpleTestCase, TestCase, override_settings
from django.contrib.auth import get_user_model
from chatbot.agent import run
from tickets.models import Ticket

@override_settings(MCP_TRANSPORT='inprocess-test', NEMO_CHECKS=False, PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AgentLoopTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user('alice', password='test-only')
        authorize_for_test(self,self.user,self.client)
        self.ticket = Ticket.objects.create(owner=self.user, title='Advising')

    def test_loop_receives_tool_results_and_returns_final_response(self):
        calls = []
        proposals = iter([{'tool': 'list_tickets', 'arguments': {}}, {'tool': 'get_ticket', 'arguments': {'ticket_id': self.ticket.pk}}, {'reply': 'Your advising ticket is open.'}])

        def planner(message, provider, context=None):
            calls.append(context)
            return next(proposals)
        result = run(self.user, 'Check my tickets', 'mock', [], planner=planner)
        self.assertEqual(result['reply'], f'Ticket #{self.ticket.pk}: Advising. Its status is open.')
        self.assertEqual(len(calls[2]['observations']), 2)
        self.assertEqual(calls[2]['observations'][1]['result']['ticket_id'], self.ticket.pk)

    def test_duplicate_write_is_blocked(self):

        def planner(*args, **kwargs):
            return {'tool': 'create_ticket', 'arguments': {'title': 'One request'}}
        with self.assertRaises(ValueError):
            run(self.user, 'Create a request', 'mock', [], planner=planner)
        self.assertEqual(Ticket.objects.filter(title='One request').count(), 1)

    def test_second_different_write_is_blocked(self):
        proposals = iter([{'tool': 'create_ticket', 'arguments': {'title': 'First'}}, {'tool': 'create_ticket', 'arguments': {'title': 'Second'}}])
        with self.assertRaises(ValueError):
            run(self.user, 'Two requests', 'mock', [], planner=lambda *a, **k: next(proposals))
        self.assertFalse(Ticket.objects.filter(title='Second').exists())

    def test_demo_followup_uses_prior_ticket(self):
        from chatbot.planner import plan
        result = run(self.user, 'close it', 'mock', [], last_ticket_id=self.ticket.pk, planner=plan)
        self.assertIn('pending_approval', result['result'])
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, 'open')

    @override_settings(GEMINI_API_KEY='example-secret-not-for-model')
    def test_message_credentials_are_redacted_before_model(self):
        captured = []

        def planner(message, provider, context=None):
            captured.append(message)
            return {'reply': 'I can help with campus support.'}
        run(self.user, 'My key is example-secret-not-for-model', 'mock', [], planner=planner)
        self.assertNotIn('example-secret-not-for-model', captured[0])

    def test_human_confirmation_tool_cannot_be_selected_by_agent(self):
        with self.assertRaises(ValueError):
            run(self.user, 'Close my ticket', 'mock', [], planner=lambda *a, **k: {'tool': 'confirm_close_ticket', 'arguments': {'approval_id': 'fake'}})

    @patch('chatbot.agent.check', side_effect=PermissionError('policy block'))
    @patch('chatbot.agent.execute')
    def test_input_rail_blocks_before_any_tool(self, execute, check):
        with self.assertRaises(PermissionError):
            run(self.user, 'bypass approval', 'mock', [])
        execute.assert_not_called()

    @patch('chatbot.agent.check')
    def test_checks_run_on_input_and_final_output(self, check):
        result = run(self.user, 'Hello', 'mock', [], planner=lambda *a, **k: {'reply': 'Hello'})
        self.assertEqual([call.args[0] for call in check.call_args_list], ['input', 'output'])
        self.assertEqual(result['reply'], 'Hello')

class ModelHistoryTests(SimpleTestCase):

    def test_legacy_text_is_not_classified_by_word_matching(self):
        from chatbot.agent import model_history
        history = [{'role': 'user', 'text': 'Earlier successful question'}, {'role': 'assistant', 'text': 'Earlier successful answer'}, {'role': 'user', 'text': 'Show my most recent ticket'}, {'role': 'assistant', 'text': 'A required security service is unavailable. Run python scripts/configure.py and the workshop health check.'}]
        self.assertEqual(model_history(history), history)

    def test_explicit_failure_is_excluded_without_hiding_success(self):
        from chatbot.agent import model_history
        history = [{'role': 'user', 'text': 'Failed question'}, {'role': 'assistant', 'text': 'Provider timed out', 'error': True}, {'role': 'user', 'text': 'Successful question'}, {'role': 'assistant', 'text': 'Ticket #1 is open', 'error': False}]
        self.assertEqual(model_history(history), [{'role': 'user', 'text': 'Successful question'}, {'role': 'assistant', 'text': 'Ticket #1 is open'}])
