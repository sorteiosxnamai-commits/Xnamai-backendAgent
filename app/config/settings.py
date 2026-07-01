import os
from dotenv import load_dotenv

load_dotenv()

MERCOS_APPLICATION_TOKEN = os.getenv("MERCOS_APPLICATION_TOKEN")
MERCOS_COMPANY_TOKEN = os.getenv("MERCOS_COMPANY_TOKEN")
MERCOS_BASE_URL = os.getenv("MERCOS_BASE_URL")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
AUTH_RESET_DEBUG = os.getenv("AUTH_RESET_DEBUG", "true").lower() == "true"
JWT_SECRET = os.getenv("JWT_SECRET", "xnamai_secret_key_dev_only")
JWT_ALGORITHM = "HS256"

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "PulseDesk")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def cors_origins() -> list[str]:
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
    ]
    if FRONTEND_URL:
        origins.append(FRONTEND_URL.rstrip("/"))
    extra = os.getenv("CORS_ORIGINS", "")
    for origin in extra.split(","):
        origin = origin.strip()
        if origin:
            origins.append(origin.rstrip("/"))
    return list(dict.fromkeys(origins))
