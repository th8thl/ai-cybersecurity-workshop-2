"""Store ticket attachments privately and open them through authenticated views."""
from pathlib import Path
from uuid import uuid4
from django.conf import settings
from .models import Attachment, AuditEvent


def attachment_folder(ticket):
    return Path(settings.MEDIA_ROOT) / 'attachments' / str(ticket.pk)


def save_attachment(actor, ticket, upload):
    folder = attachment_folder(ticket)
    folder.mkdir(parents=True, exist_ok=True)
    storage_name = uuid4().hex
    target = folder / storage_name
    try:
        written = 0
        with target.open('xb') as destination:
            for chunk in upload.chunks():
                written += len(chunk)
                if written > settings.TICKET_MAX_ATTACHMENT_BYTES:
                    raise ValueError('The attachment is too large. Choose a file no larger than 2 MB.')
                destination.write(chunk)
        record = Attachment.objects.create(ticket=ticket, uploaded_by=actor,
            original_name=Path(upload.name).name[:255], storage_name=storage_name, size=written)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    AuditEvent.objects.create(actor=actor, tool='upload_attachment', outcome='saved')
    return record


def open_attachment(ticket, name):
    folder = attachment_folder(ticket)
    record = Attachment.objects.filter(ticket=ticket, storage_name=name).first()
    # Workshop repair: a name containing ../ can reach another ticket's folder.
    stream = (folder / name).open('rb')
    return stream, record.original_name if record else Path(name).name
