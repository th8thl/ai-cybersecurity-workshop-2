"""Consent and delegated access are enforced in both workshop implementations."""
from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from chatbot.models import MCPAccessGrant
from tickets.models import Ticket
from chatbot.mcp_client import call, discover
from security.mcp_authorization import (issue_grant, validate_token, use_access_token,
    COOKIE_NAME, PERMISSIONS, CLIENT_ID, AUDIENCE, MCPAuthorizationError)
from security.redaction import sanitize


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
                   MCP_TRANSPORT='inprocess-test',NEMO_CHECKS=False)
class AuthorizationTests(TestCase):
    def setUp(self):
        self.alice=get_user_model().objects.create_user('consent-alice')
        self.bob=get_user_model().objects.create_user('consent-bob')
        self.ticket=Ticket.objects.create(owner=self.alice,title='My ticket')
        self.client.force_login(self.alice)

    def grant(self,permissions=None,client=None):
        client=client or self.client
        response=client.post('/chatbot/authorization/', {'decision':'allow',
            'permissions':permissions or ['tickets:read'],'duration':'1800'})
        self.assertEqual(response.status_code,200)
        return response,response.cookies[COOKIE_NAME].value

    def test_opening_assistant_or_consent_does_not_issue_token(self):
        self.assertContains(self.client.get('/chatbot/'),'Authorize assistant')
        self.assertContains(self.client.get('/chatbot/authorization/'),'Read my tickets')
        self.assertFalse(MCPAccessGrant.objects.exists())

    @patch('chatbot.views.plan',side_effect=AssertionError('Consent must precede model calls'))
    def test_without_consent_ticket_pages_work_but_assistant_cannot_act(self,planner):
        self.assertEqual(self.client.get('/tickets/').status_code,200)
        self.assertEqual(self.client.get(f'/tickets/{self.ticket.pk}/').status_code,200)
        self.assertEqual(self.client.post('/tickets/new/',{'title':'Without assistant'}).status_code,302)
        response=self.client.post('/chatbot/',{'message':'create ticket Not authorized','provider':'mock'})
        self.assertContains(response,'Authorize the assistant')
        self.assertFalse(Ticket.objects.filter(title='Not authorized').exists())
        planner.assert_not_called()

    def test_deny_does_not_issue_token(self):
        response=self.client.post('/chatbot/authorization/',{'decision':'deny'})
        self.assertEqual(response.status_code,302)
        self.assertFalse(MCPAccessGrant.objects.exists())
        self.assertFalse(response.cookies[COOKIE_NAME].value)

    def test_consent_stores_hash_and_binds_token_to_user_client_audience(self):
        response,token=self.grant()
        grant=MCPAccessGrant.objects.get()
        self.assertEqual(grant.user,self.alice)
        self.assertEqual(grant.client_id,CLIENT_ID)
        self.assertEqual(grant.audience,AUDIENCE)
        self.assertEqual(grant.scopes,['tickets:read'])
        self.assertNotEqual(grant.token_hash,token)
        self.assertNotIn(token,repr(list(MCPAccessGrant.objects.values())))
        self.assertEqual(validate_token(token).pk,grant.pk)
        self.assertTrue(response.cookies[COOKIE_NAME]['httponly'])
        self.assertEqual(response.cookies[COOKIE_NAME]['samesite'],'Lax')
        self.assertEqual(response.cookies[COOKIE_NAME]['path'],'/chatbot/')
        self.assertIn('no-store',response['Cache-Control'])
        self.assertContains(response,token)
        self.assertNotContains(self.client.get('/chatbot/authorization/'),token)

    def test_read_only_grant_allows_read_and_denies_create(self):
        _,token=self.grant()
        with use_access_token(token):
            self.assertEqual(call(self.alice,'get_ticket',{'ticket_id':self.ticket.pk})['ticket_id'],self.ticket.pk)
            self.assertEqual({t['name'] for t in discover(self.alice)['tools']},{'list_tickets','get_ticket'})
            with self.assertRaises(MCPAuthorizationError):call(self.alice,'create_ticket',{'title':'Denied'})
        response=self.client.post('/chatbot/',{'message':'create ticket Denied','provider':'mock'})
        self.assertContains(response,'You have not authorized this permission')
        self.assertFalse(Ticket.objects.filter(title='Denied').exists())

    def test_user_can_grant_create_permission(self):
        self.grant(['tickets:read','tickets:create'])
        response=self.client.post('/chatbot/',{'message':'create ticket Authorized','provider':'mock'})
        self.assertContains(response,'Authorized')
        self.assertTrue(Ticket.objects.filter(owner=self.alice,title='Authorized').exists())

    def test_revoke_invalidates_old_token_without_breaking_tickets(self):
        _,token=self.grant()
        self.assertEqual(self.client.post('/chatbot/authorization/revoke/').status_code,302)
        with self.assertRaisesMessage(MCPAuthorizationError,'revoked'):validate_token(token)
        self.assertEqual(self.client.get(f'/tickets/{self.ticket.pk}/').status_code,200)

    def test_expired_token_is_rejected(self):
        _,token=self.grant()
        MCPAccessGrant.objects.update(expires_at=timezone.now()-timedelta(seconds=1))
        with self.assertRaisesMessage(MCPAuthorizationError,'expired'):validate_token(token)
        response=self.client.post('/chatbot/',{'message':'get ticket 1','provider':'mock'})
        self.assertContains(response,'access expired')

    def test_new_consent_replaces_previous_token(self):
        _,old=self.grant()
        _,new=self.grant(['tickets:read','tickets:create'])
        with self.assertRaises(MCPAuthorizationError):validate_token(old)
        self.assertEqual(validate_token(new).scopes,['tickets:create','tickets:read'])
        self.assertEqual(MCPAccessGrant.objects.filter(revoked_at__isnull=True).count(),1)

    def test_each_user_has_separate_authorization_and_revocation(self):
        _,alice_token=self.grant()
        bob_client=Client();bob_client.force_login(self.bob)
        _,bob_token=self.grant(client=bob_client)
        self.assertNotEqual(alice_token,bob_token)
        self.client.post('/chatbot/authorization/revoke/')
        self.assertEqual(validate_token(bob_token).user,self.bob)
        with self.assertRaises(MCPAuthorizationError):validate_token(bob_token,expected_user_id=self.alice.pk)

    def test_wrong_client_or_audience_is_rejected(self):
        _,token=self.grant()
        MCPAccessGrant.objects.update(audience='another-server')
        with self.assertRaises(MCPAuthorizationError):validate_token(token)
        MCPAccessGrant.objects.update(audience=AUDIENCE,client_id='another-client')
        with self.assertRaises(MCPAuthorizationError):validate_token(token)

    def test_revoked_or_invalid_tokens_cannot_be_used(self):
        for token in (None,'forged','mcp_'+'x'*43):
            with self.subTest(token=token),self.assertRaises(MCPAuthorizationError):validate_token(token)

    def test_unknown_permissions_and_duration_do_not_issue_grant(self):
        for permissions,duration in [(['tickets:confirm-close'],'1800'),(['tickets:read'],'999999'),([], '1800')]:
            response=self.client.post('/chatbot/authorization/',{'decision':'allow','permissions':permissions,'duration':duration})
            self.assertEqual(response.status_code,200)
            self.assertFalse(MCPAccessGrant.objects.exists())

    def test_consent_requires_login_and_csrf_revoke_requires_post(self):
        anonymous=Client()
        self.assertEqual(anonymous.get('/chatbot/authorization/').status_code,302)
        strict=Client(enforce_csrf_checks=True);strict.force_login(self.alice)
        self.assertEqual(strict.post('/chatbot/authorization/',{'decision':'allow'}).status_code,403)
        self.assertEqual(strict.post('/chatbot/authorization/revoke/').status_code,403)
        self.assertEqual(self.client.get('/chatbot/authorization/revoke/').status_code,405)

    def test_client_cannot_call_confirmation_tool(self):
        _,token=self.grant(list(PERMISSIONS))
        with use_access_token(token):
            with self.assertRaises(PermissionError):call(self.alice,'confirm_close_ticket',{'approval_id':'anything'})

    def test_token_is_redacted_from_prompts_and_diagnostics(self):
        _,token=self.grant()
        with use_access_token(token):self.assertEqual(sanitize({'token':token}),{'token':'[REDACTED]'})
        response=self.client.post('/chatbot/',{'message':'Show my most recent ticket','provider':'mock'})
        self.assertNotContains(response,token)

    def test_same_origin_consent_form_passes_csrf_and_keeps_referrer_private(self):
        strict=Client(enforce_csrf_checks=True)
        strict.force_login(self.alice)
        page=strict.get('/chatbot/authorization/')
        self.assertEqual(page['Referrer-Policy'],'same-origin')
        response=strict.post('/chatbot/authorization/', {
            'decision':'allow','permissions':['tickets:read'],'duration':'1800',
            'csrfmiddlewaretoken':strict.cookies['csrftoken'].value,
        },HTTP_ORIGIN='http://testserver')
        self.assertEqual(response.status_code,200)
        self.assertIn(COOKIE_NAME,response.cookies)
