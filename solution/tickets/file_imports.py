"""Read uploaded JSON ticket files as data, without executing Python objects."""
import json


def load_ticket_file(upload):
    if not upload.name.lower().endswith('.json'):
        raise ValueError('Only JSON ticket files are accepted.')
    try:
        data = json.loads(upload.read().decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError('Cannot import this file because it is not valid JSON.') from exc
    return validate_ticket_data(data)

def validate_ticket_data(data):
    if not isinstance(data, dict) or set(data) != {"title"}:
        raise ValueError('The ticket file must contain exactly one field: title.')
    title = data["title"]
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
        raise ValueError('The title must contain between 1 and 120 characters.')
    return {"title": title.strip()}
