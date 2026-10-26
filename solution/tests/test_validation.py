from .common import TicketTestCase
from tickets.models import Ticket
from chatbot.tool_policy import execute

class SecurityTests(TicketTestCase):

    def test_extra_keys_and_wrong_types_rejected(self):
        for p in [dict(self.proposal(), approved=True), {'tool': 'get_ticket', 'arguments': {'ticket_id': str(self.own.pk)}}, {'tool': 'get_ticket', 'arguments': {'ticket_id': True}}, {'tool': 'create_ticket', 'arguments': {'title': '   '}}, {'tool': 'create_ticket', 'arguments': {'title': 'x', 'owner': self.bob.pk}}]:
            with self.subTest(p=p), self.assertRaises(ValueError):
                execute(self.alice, p)

    def test_unknown_tool_rejected(self):
        with self.assertRaises(ValueError):
            execute(self.alice, {'tool': 'run_shell', 'arguments': {}})

    def test_create_owner_comes_from_session(self):
        result = execute(self.alice, {'tool': 'create_ticket', 'arguments': {'title': 'Need help'}})
        self.assertEqual(Ticket.objects.get(pk=result['ticket_id']).owner, self.alice)
