from unittest.mock import patch
from django.test import SimpleTestCase, override_settings
from security.redaction import sanitize
from tickets.schema import validate_step


class ContextSecurityTests(SimpleTestCase):
    @override_settings(NEMO_CHECKS=True)
    @patch('guardrails.runtime._worker',None)
    @patch('guardrails.runtime._start',side_effect=OSError('worker unavailable'))
    def test_nemo_worker_start_failure_is_fail_closed(self,start):
        from guardrails.runtime import check, GuardrailBlocked
        with self.assertRaises(GuardrailBlocked):check('input','Hello')

    @override_settings(GEMINI_API_KEY='example-provider-secret-for-test',SECRET_KEY='test-django-secret')
    def test_redaction_prevents_credentials_entering_context(self):
        self.assertEqual(sanitize('example-provider-secret-for-test'),'[REDACTED]')
        self.assertEqual(sanitize({'message':'test-django-secret'}),{'message':'[REDACTED]'})
        self.assertEqual(sanitize('mcp_'+'a'*43),'[REDACTED]')

    def test_schema_never_exposes_user_or_approval_claims(self):
        for proposal in [{'tool':'get_ticket','arguments':{'ticket_id':1,'actor':2}},
                         {'tool':'confirm_close_ticket','arguments':{'approval_id':'forged'}},
                         {'reply':'okay','approved':True}]:
            with self.subTest(proposal=proposal),self.assertRaises(ValueError):validate_step(proposal)
