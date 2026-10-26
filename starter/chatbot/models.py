import uuid
from django.conf import settings
from django.db import models


class ChatMessage(models.Model):
    session_key = models.CharField(max_length=64, blank=True)
    role = models.CharField(max_length=20)
    content = models.TextField()
    provider = models.CharField(max_length=40, blank=True)
    model = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M:%S} {self.role}"



class MCPAccessGrant(models.Model):
    """Only the hash is stored; the client receives the raw token after consent."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    client_id = models.CharField(max_length=80)
    audience = models.CharField(max_length=80)
    token_hash = models.CharField(max_length=64, unique=True)
    scopes = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user','client_id'],
            condition=models.Q(revoked_at__isnull=True), name='one_active_mcp_grant_per_user_client')]
