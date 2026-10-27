"""Exercise 5: connect to MCP and discover its tools."""
import os
import sys
from pathlib import Path
from getpass import getpass

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "support_portal.settings")
import django
django.setup()

from django.contrib.auth import get_user_model
from chatbot.mcp_client import discover
from security.mcp_authorization import use_access_token

alice = get_user_model().objects.get(username="alice")
token = getpass("Paste Alice's authorized token (hidden): ")
with use_access_token(token):
    service = discover(alice)

print(service["server"])
print([tool["name"] for tool in service["tools"]])
