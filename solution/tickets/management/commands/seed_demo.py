"""Create demo accounts and show their setup-generated passwords."""
import secrets
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from dotenv import dotenv_values, set_key
from tickets.models import Ticket


class Command(BaseCommand):
    help = "Create demo accounts; --show-passwords only displays saved demo logins."

    def add_arguments(self, parser):
        parser.add_argument('--reset-passwords', action='store_true', help='Explicitly generate, save and print new Alice/Bob demo passwords.')
        parser.add_argument('--show-passwords', action='store_true', help='Show saved setup passwords without changing accounts or tickets.')

    def handle(self, *args, **options):
        env_file = settings.BASE_DIR / '.env'
        saved = dotenv_values(env_file) if env_file.exists() else {}
        for name in ('alice', 'bob'):
            if options['show_passwords']:
                user = get_user_model().objects.filter(username=name).first()
                if user is None:
                    self.stdout.write(f'{name}: account not created; run python manage.py seed_demo.')
                    continue
            else:
                user, created = get_user_model().objects.get_or_create(username=name)
                if created or options["reset_passwords"]:
                    password = secrets.token_urlsafe(12)
                    user.set_password(password)
                    user.save()
                    key = f'DEMO_{name.upper()}_PASSWORD'
                    set_key(str(env_file), key, password)
                    saved[key] = password
            password = saved.get(f'DEMO_{name.upper()}_PASSWORD')
            if password and user.check_password(password):
                self.stdout.write(f'{name} password: {password}')
            else:
                self.stdout.write(f'{name}: existing password was not saved by this setup, or was changed. Set it with: python manage.py changepassword {name}')
            if not options['show_passwords']:
                ticket, _ = Ticket.objects.get_or_create(owner=user, title=f'{name.title()}: support request')
                self.stdout.write(f'{name}: ticket {ticket.pk}')
