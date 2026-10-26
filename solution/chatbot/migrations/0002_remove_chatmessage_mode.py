from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("chatbot", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="chatmessage",
            name="mode",
        ),
    ]
