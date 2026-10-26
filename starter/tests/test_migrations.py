"""Check that the package rename preserves an existing workshop database."""
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from django.conf import settings
from django.test import SimpleTestCase


class TicketMigrationTests(SimpleTestCase):
    def test_existing_ticket_data_survives_app_rename(self):
        with tempfile.TemporaryDirectory(prefix="ticket-migration-test-") as directory:
            database = Path(directory) / "workshop.sqlite3"
            env = os.environ.copy()
            env["WORKSHOP_RUNTIME_DB"] = str(database)
            env["DJANGO_SECRET_KEY"] = "disposable-migration-test-key"

            def run(*arguments):
                result = subprocess.run(
                    [sys.executable, "manage.py", *arguments],
                    cwd=settings.BASE_DIR, env=env, capture_output=True, text=True,
                    timeout=60,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            def snapshot():
                with closing(sqlite3.connect(database)) as db:
                    names = ["auth_user", "auth_permission", "auth_user_user_permissions",
                             "django_content_type", "tickets_ticket", "tickets_approval",
                             "tickets_auditevent"]
                    return {name: db.execute('SELECT * FROM "' + name + '" ORDER BY 1').fetchall()
                            for name in names}

            run("migrate", "--noinput", "--skip-checks")
            run("shell", "-c", "from django.contrib.auth import get_user_model; "
                "from django.contrib.auth.models import Permission; "
                "from tickets.models import Ticket, Approval, AuditEvent; "
                "user = get_user_model().objects.create_user('migration-alice', password='test-only'); "
                "user.user_permissions.add(Permission.objects.get(content_type__app_label='tickets', codename='view_ticket')); "
                "ticket = Ticket.objects.create(owner=user, title='Preserve this ticket'); "
                "Approval.objects.create(actor=user, ticket=ticket); "
                "AuditEvent.objects.create(actor=user, tool='get_ticket', outcome='executed')")
            before = snapshot()

            # Reproduce the previous app's table names and migration history.
            with closing(sqlite3.connect(database)) as db:
                db.execute("DROP TABLE IF EXISTS tickets_attachment")
                for name in ("ticket", "approval", "auditevent"):
                    db.execute('ALTER TABLE "tickets_' + name + '" RENAME TO "actions_' + name + '"')
                db.execute("UPDATE django_content_type SET app_label='actions' WHERE app_label='tickets' AND model IN ('ticket','approval','auditevent')")
                db.execute("DELETE FROM django_migrations WHERE app='tickets'")
                db.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('actions', '0001_initial', CURRENT_TIMESTAMP)")
                db.commit()

            run("migrate", "--noinput", "--skip-checks")
            self.assertEqual(snapshot(), before)
            run("migrate", "--noinput", "--skip-checks")
            self.assertEqual(snapshot(), before)
            with closing(sqlite3.connect(database)) as db:
                self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])
