"""Explicit authorizations for tests of unrelated assistant features."""
from security.mcp_authorization import issue_grant, use_access_token, COOKIE_NAME, PERMISSIONS


def authorize_for_test(test, user, client=None):
    grant, token = issue_grant(user, list(PERMISSIONS))
    test.enterContext(use_access_token(token))
    if client is not None:
        client.cookies[COOKIE_NAME] = token
    return token
