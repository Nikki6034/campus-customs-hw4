"""Configuration read from environment variables.

The API key is never hard-coded. It is read from the environment, which is
populated from (in order of precedence):

  1. real environment variables already set in your shell
  2. backend/.env          - this assignment's own overrides
  3. ../.env               - the shared AI Foundations key

Matches the Portkey gateway setup used in the earlier homework.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
COURSE_ROOT = PROJECT_ROOT.parent

# Sources in priority order (override=False keeps earlier wins):
#   backend/.env  →  <project root>/.env  →  one level up (shared key).
load_dotenv(BACKEND_DIR / ".env", override=False)
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(COURSE_ROOT / ".env", override=False)
DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / "data"))
DB_PATH = Path(os.getenv("DB_PATH", DATA_DIR / "campus_customs.db"))
PRODUCT_IMAGE_DIR = DATA_DIR / "products"

# Append-only audit log of agent loop activity.
AUDIT_PATH = Path(os.getenv("AUDIT_PATH", PROJECT_ROOT / "output" / "audit_trail.json"))

PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")
PORTKEY_PROVIDER = os.getenv("PORTKEY_PROVIDER", "openai")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

# "agent" routes chat through the Pydantic AI agent (Problem 5, the default).
# "stub" returns a canned reply without calling a model (useful offline).
CHAT_MODE = os.getenv("CHAT_MODE", "agent").strip().lower()

# Vite's dev server runs on 5173 by default.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]


def get_api_key() -> str | None:
    """Return the Portkey API key, or None when it is not configured."""
    return os.getenv("API_PORTKEY_API_KEY") or os.getenv("PORTKEY_API_KEY") or None


def require_api_key() -> str:
    """Return the Portkey API key, raising if it is missing."""
    key = get_api_key()
    if not key:
        raise RuntimeError(
            "No Portkey API key found. Set API_PORTKEY_API_KEY or "
            "PORTKEY_API_KEY in backend/.env, or export it in your shell."
        )
    return key
