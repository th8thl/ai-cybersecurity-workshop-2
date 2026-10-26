import secrets
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from tickets.models import Ticket

class Command(BaseCommand):
    help = "Create synthetic lab users and tickets. Existing users are never reset."
    def handle(self, *args, **options):
        for name in ("alice", "bob"):
            user, created = get_user_model().objects.get_or_create(username=name)
            if created:
                password = secrets.token_urlsafe(12)
                user.set_password(password)
                user.save()
                self.stdout.write(f"{name} password: {password} (save for this lab)")
            ticket, _ = Ticket.objects.get_or_create(owner=user, title=f"{name.title()}: advising request")
            self.stdout.write(f"{name}: ticket {ticket.pk}")
