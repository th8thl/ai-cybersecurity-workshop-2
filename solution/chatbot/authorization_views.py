"""Explicit user consent, token delivery and revocation for the local MCP client."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from tickets.models import AuditEvent
from security.mcp_authorization import (CLIENT_NAME, COOKIE_NAME, PERMISSIONS,
    authorization_status, issue_grant, revoke_grants)
from .forms import AssistantAuthorizationForm


@never_cache
@login_required
def authorize_assistant(request):
    grant, error = authorization_status(request.user)
    form = AssistantAuthorizationForm(initial={'permissions':grant.scopes if grant else ['tickets:read']})
    token = None
    if request.method == 'POST':
        if request.POST.get('decision') == 'deny':
            revoke_grants(request.user)
            AuditEvent.objects.create(actor=request.user,tool='authorize_assistant',outcome='denied')
            messages.info(request,'Assistant access was not granted. You can continue using the ticket pages.')
            response = redirect('assistant')
            response.delete_cookie(COOKIE_NAME,path='/chatbot/')
            return response
        if request.POST.get('decision') != 'allow':
            form = AssistantAuthorizationForm(request.POST)
            form.is_valid()
            form.add_error(None,'Choose Authorize assistant or Deny access.')
        else:
            form = AssistantAuthorizationForm(request.POST)
            if form.is_valid():
                grant, token = issue_grant(request.user,form.cleaned_data['permissions'],form.cleaned_data['duration'])
                AuditEvent.objects.create(actor=request.user,tool='authorize_assistant',outcome='granted')
                error = None
    response = render(request,'chatbot/authorization.html',{'form':form,'authorization':grant,
        'authorization_error':error,'client_name':CLIENT_NAME,'issued_token':token,
        'permission_labels':[PERMISSIONS[p] for p in grant.scopes] if grant else []})
    if token:
        response.set_cookie(COOKIE_NAME,token,max_age=form.cleaned_data['duration'],
            httponly=True,secure=request.is_secure(),samesite='Lax',path='/chatbot/')
    response['Referrer-Policy'] = 'same-origin'
    return response


@never_cache
@login_required
@require_POST
def revoke_assistant(request):
    revoke_grants(request.user)
    AuditEvent.objects.create(actor=request.user,tool='authorize_assistant',outcome='revoked')
    messages.success(request,'Assistant access revoked. Your ticket pages still work.')
    response = redirect('assistant_authorization')
    response.delete_cookie(COOKIE_NAME,path='/chatbot/')
    return response
