"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


class Config:
    """Default configuration for MovieScope."""

    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        if os.getenv("VERCEL") == "1":
            raise RuntimeError("Set SECRET_KEY in the Vercel project environment.")
        SECRET_KEY = "moviescope-dev-secret-change-me"

    # PostgreSQL connection string (Neon provides this as DATABASE_URL).
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    SESSION_COOKIE_SECURE = os.getenv("VERCEL") == "1"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Demo session: the app ships without authentication and uses a seeded user.
    DEMO_USER_ID = _env_int("DEMO_USER_ID", 1)

    # Recommendation tuning
    MIN_RATING_COUNT = _env_int("MIN_RATING_COUNT", 10)

    GENRES = [
        "Action",
        "Animation",
        "Comedy",
        "Crime",
        "Drama",
        "Horror",
        "Romance",
        "Sci-Fi",
        "Thriller",
        "Western",
    ]

    # Number of movies shown per page section
    RECOMMENDATION_LIMIT = 6
    TOP_RATED_MIN_COUNT = 3
