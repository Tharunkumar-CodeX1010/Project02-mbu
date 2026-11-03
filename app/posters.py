"""Poster resolution.

MovieScope ships a small local cache of real posters so the UI never depends on
a third-party image host during a demo. Resolution order:

1. the bundled local JPEG when it matches the movie's stored remote URL,
2. the stored remote URL,
3. the generated MovieScope SVG cover (always available locally).
"""

import json
from pathlib import Path

from flask import current_app, url_for

POSTER_DIRECTORY = "img/posters"
REAL_POSTER_DIRECTORY = f"{POSTER_DIRECTORY}/real"
REAL_POSTER_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")


def _value(movie, key):
    """Templates receive dict rows from PostgreSQL and dicts from analysis."""
    if isinstance(movie, dict):
        return movie.get(key)
    return getattr(movie, key, None)


def _manifest():
    cached = current_app.extensions.get("poster_manifest")
    if cached is not None:
        return cached

    folder = Path(current_app.static_folder) / REAL_POSTER_DIRECTORY
    manifest_path = folder / "manifest.json"
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = {str(key): value for key, value in raw.items()}
    except (OSError, ValueError, AttributeError):
        # Do not cache a miss: the cache may be installed while the app runs.
        return {}

    current_app.extensions["poster_manifest"] = manifest
    return manifest


def poster_source(movie):
    """Return the best available poster URL for a movie row."""
    movie_id = _value(movie, "movie_id")
    remote = _value(movie, "poster_url")

    if movie_id is not None:
        key = str(movie_id)
        folder = Path(current_app.static_folder) / REAL_POSTER_DIRECTORY
        cached_url = _manifest().get(key)
        for suffix in REAL_POSTER_SUFFIXES:
            cache_file = folder / f"{key}{suffix}"
            if not cache_file.is_file():
                continue
            # A freshly added or edited URL should win over the bundled image.
            if remote is None or cached_url is None or remote == cached_url:
                return url_for(
                    "static", filename=f"{REAL_POSTER_DIRECTORY}/{cache_file.name}"
                )
            break

    if isinstance(remote, str) and remote.startswith(("http://", "https://")):
        return remote

    return url_for("static", filename=f"{POSTER_DIRECTORY}/{movie_id}.svg")
