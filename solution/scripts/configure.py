"""Configure this app only, preserving existing secrets and settings."""
from pathlib import Path
from django.core.management.utils import get_random_secret_key
from dotenv import dotenv_values, set_key

def configure():
    root = Path(__file__).resolve().parents[1]
    path = root / ".env"
    if not path.exists():
        path.write_text((root / ".env.example").read_text(encoding="utf-8"), encoding="utf-8")
    current = dotenv_values(path)
    for key, value in dotenv_values(root / ".env.example").items():
        if key not in current:
            set_key(str(path), key, value or "")
    if not current.get("DJANGO_SECRET_KEY"):
        set_key(str(path), "DJANGO_SECRET_KEY", get_random_secret_key())
    print("Local settings are saved in .env; existing values were preserved.")
    print("Assistant access is granted by each user at /chatbot/authorization/ after signing in.")

if __name__ == "__main__":
    configure()
