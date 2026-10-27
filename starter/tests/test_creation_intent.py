"""Explicit creation must not silently become an unrelated read."""
import json
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from chatbot.agent import run
from chatbot.planner import plan
from security.mcp_authorization import issue_grant, use_access_token, MCPAuthorizationError
from tickets.models import Ticket

MESSAGE = 'Create a new ticket for bringing markers to the classroom'


@override_settings(NEMO_CHECKS=False, MCP_TRANSPORT='inprocess-test')
class CreationIntentTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('creation-user')
        self.ticket = Ticket.objects.create(owner=self.user, title='Existing ticket')

    def test_read_only_grant_denies_without_planning_or_reading(self):
        _, token = issue_grant(self.user, ['tickets:read'])
        with use_access_token(token), patch('chatbot.agent.discover') as discovery:
            planner = MagicMock()
            with self.assertRaises(MCPAuthorizationError) as caught:
                run(self.user, MESSAGE, 'qwen', [], planner=planner)
            self.assertEqual(caught.exception.code, 'insufficient_permission')
            planner.assert_not_called()
            discovery.assert_not_called()
        self.assertEqual(Ticket.objects.count(), 1)

    @patch('chatbot.planner.request.urlopen')
    def test_creation_schema_cannot_select_a_read(self, urlopen):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({'message':{'content':json.dumps({'tool':'create_ticket','arguments':{'title':'Markers'}})}}).encode()
        urlopen.return_value = response
        plan(MESSAGE, 'qwen', context={'tools':[{'name':'list_tickets'},{'name':'get_ticket'},{'name':'create_ticket'}]})
        schema = json.loads(urlopen.call_args.args[0].data)['format']
        operations = [b['properties']['tool']['const'] for b in schema['anyOf'] if 'tool' in b['properties']]
        self.assertEqual(operations, ['create_ticket'])

    def test_wrong_model_operation_cannot_execute(self):
        _, token = issue_grant(self.user, ['tickets:read', 'tickets:create'])
        with use_access_token(token), patch('chatbot.agent.execute') as execute:
            with self.assertRaises(ValueError):
                run(self.user, MESSAGE, 'qwen', [], planner=lambda *a, **k: {'tool':'get_ticket','arguments':{'ticket_id':self.ticket.pk}})
            execute.assert_not_called()
