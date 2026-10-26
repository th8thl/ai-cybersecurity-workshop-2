"""Read ticket imports. Python pickle support is intentionally unsafe."""
import json
import pickle


def load_ticket_file(upload):
    contents = upload.read()
    if upload.name.lower().endswith('.pkl'):
        # Workshop repair: unpickling an uploaded file may execute its instructions.
        try:
            data = pickle.loads(contents)
        except Exception as exc:
            raise ValueError('Cannot read this Python pickle ticket file.') from exc
    else:
        try:
            data = json.loads(contents.decode('utf-8'))
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
