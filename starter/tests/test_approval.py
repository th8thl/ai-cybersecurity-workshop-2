from .common import TicketTestCase
from tickets.models import Approval
from chatbot.tool_policy import execute
from tickets.ticket_service import approve
from django.utils import timezone
from datetime import timedelta

class SecurityTests(TicketTestCase):

    def test_close_requires_approval_and_replay_fails(self):
        result = execute(self.alice, self.proposal('close_ticket'))
        self.assertIn('pending_approval', result, 'Closing must create a pending approval')
        self.own.refresh_from_db()
        self.assertEqual(self.own.status, 'open')
        approve(self.alice, result['pending_approval'])
        self.own.refresh_from_db()
        self.assertEqual(self.own.status, 'closed')
        with self.assertRaises(PermissionError):
            approve(self.alice, result['pending_approval'])

    def test_approval_is_bound_to_actor(self):
        result = execute(self.alice, self.proposal('close_ticket'))
        self.assertIn('pending_approval', result, 'Closing must create a pending approval')
        with self.assertRaises(PermissionError):
            approve(self.bob, result['pending_approval'])

    def test_expired_approval_rejected(self):
        result = execute(self.alice, self.proposal('close_ticket'))
        self.assertIn('pending_approval', result, 'Closing must create a pending approval')
        Approval.objects.filter(pk=result['pending_approval']).update(created_at=timezone.now() - timedelta(minutes=6))
        with self.assertRaises(PermissionError):
            approve(self.alice, result['pending_approval'])

    def test_ownership_rechecked_at_execution(self):
        result = execute(self.alice, self.proposal('close_ticket'))
        self.assertIn('pending_approval', result, 'Closing must create a pending approval')
        self.own.owner = self.bob
        self.own.save()
        with self.assertRaises(PermissionError):
            approve(self.alice, result['pending_approval'])

    def test_http_approval_requires_explicit_confirmation(self):
        self.client.force_login(self.alice)
        result = execute(self.alice, self.proposal('close_ticket'))
        self.assertIn('pending_approval', result, 'Closing must create a pending approval')
        self.client.post(f'/tickets/{self.own.pk}/', {'approval_id':result['pending_approval']})
        self.own.refresh_from_db()
        self.assertEqual(self.own.status, 'open')
        self.client.post(f'/tickets/{self.own.pk}/', {'ticket_action':'confirm','approval_id':result['pending_approval']})
        self.own.refresh_from_db()
        self.assertEqual(self.own.status, 'closed')
