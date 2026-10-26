from .common import TicketTestCase
from chatbot.tool_policy import execute

class SecurityTests(TicketTestCase):

    def test_own_ticket_read(self):
        self.assertEqual(execute(self.alice, self.proposal())['ticket_id'], self.own.pk)

    def test_cross_user_read_rejected(self):
        with self.assertRaises(PermissionError):
            execute(self.alice, self.proposal(ticket=self.other))

    def test_cross_user_close_rejected(self):
        with self.assertRaises(PermissionError):
            execute(self.alice, self.proposal('close_ticket', self.other))
        self.other.refresh_from_db()
        self.assertEqual(self.other.status, 'open')
