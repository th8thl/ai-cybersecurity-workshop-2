from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("tickets", "0002_attachment")]
    operations = [migrations.DeleteModel(name="Attachment")]
