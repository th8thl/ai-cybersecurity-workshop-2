"""Temporary accounts and tickets shared by the permission tests."""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from tickets.models import Ticket
from .authorization_helpers import authorize_for_test

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'], MCP_TRANSPORT='inprocess-test', NEMO_CHECKS=False)
class TicketTestCase(TestCase):

    def setUp(self):
        self.alice = get_user_model().objects.create_user('alice', password='test-only-password')
        self.bob = get_user_model().objects.create_user('bob', password='test-only-password')
        self.own = Ticket.objects.create(owner=self.alice, title='Advising')
        self.other = Ticket.objects.create(owner=self.bob, title='Private synthetic ticket')
        authorize_for_test(self,self.alice,self.client)

    def proposal(self, tool='get_ticket', ticket=None):
        return {'tool': tool, 'arguments': {'ticket_id': (ticket or self.own).pk}}
