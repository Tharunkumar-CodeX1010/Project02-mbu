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
    """Default configuration for the MovieScope prototype."""

    SECRET_KEY = os.getenv("SECRET_KEY", "moviescope-dev-secret-change-me")

    # MySQL connection
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = _env_int("DB_PORT", 3306)
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "moviescope")

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
