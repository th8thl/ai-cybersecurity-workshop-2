from jsonschema import Draft202012Validator

def branch(tool, properties, required):
    return {"type": "object", "properties": {"tool": {"const": tool},
        "arguments": {"type": "object", "properties": properties,
                      "required": required, "additionalProperties": False}},
        "required": ["tool", "arguments"], "additionalProperties": False}

TICKET_ID = {"type": "integer", "minimum": 1}
SCHEMA = {"$schema": "https://json-schema.org/draft/2020-12/schema", "oneOf": [
    branch("list_tickets", {}, []),
    branch("get_ticket", {"ticket_id": TICKET_ID}, ["ticket_id"]),
    branch("close_ticket", {"ticket_id": TICKET_ID}, ["ticket_id"]),
    branch("create_ticket", {"title": {"type": "string", "minLength": 1,
                                      "maxLength": 120, "pattern": r"\S"}}, ["title"]),
]}

def validate_proposal(proposal):
    if not Draft202012Validator(SCHEMA).is_valid(proposal):
        raise ValueError("Invalid action: use an allowed tool and its exact argument schema.")
    return proposal


REPLY_SCHEMA = {"type":"object", "properties":{"reply":{"type":"string","minLength":1,"maxLength":2000}},
                "required":["reply"],"additionalProperties":False}
PLAN_SCHEMA = {"anyOf": SCHEMA["oneOf"] + [REPLY_SCHEMA]}

def validate_step(value):
    if not Draft202012Validator(PLAN_SCHEMA).is_valid(value):
        raise ValueError("Model output does not match the step schema.")
    return value
