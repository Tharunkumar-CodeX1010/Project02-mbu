"""Input validation used by the rating and movie management forms."""

from datetime import date
from urllib.parse import urlparse

FIRST_FILM_YEAR = 1888  # The oldest surviving film footage is from this era.


class ValidationError(ValueError):
    """Raised when submitted form data is not acceptable."""


def clean_text(value, field, max_length, required=True):
    text = (value or "").strip()
    if required and not text:
        raise ValidationError(f"{field} is required.")
    if len(text) > max_length:
        raise ValidationError(f"{field} must be {max_length} characters or fewer.")
    return text


def parse_rating(value):
    """Ratings are whole numbers from 1 to 10, on both client and server."""
    try:
        rating = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError("Rating must be a whole number between 1 and 10.")
    if rating < 1 or rating > 10:
        raise ValidationError("Rating must be between 1 and 10.")
    return rating


def parse_release_year(value):
    current_year = date.today().year + 2  # allow announced upcoming releases
    try:
        year = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError("Release year must be a valid number.")
    if year < FIRST_FILM_YEAR or year > current_year:
        raise ValidationError(
            f"Release year must be between {FIRST_FILM_YEAR} and {current_year}."
        )
    return year


def parse_genre(value, allowed_genres):
    genre = clean_text(value, "Genre", 40)
    if genre not in allowed_genres:
        raise ValidationError("Please choose a valid genre.")
    return genre


def parse_poster_url(value):
    """Poster URLs are optional. Only http(s) links are accepted."""
    url = (value or "").strip()
    if not url:
        return None
    if len(url) > 500:
        raise ValidationError("Poster URL must be 500 characters or fewer.")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValidationError("Poster URL must start with http:// or https://.")
    return url


def parse_movie_form(form, allowed_genres):
    """Validate and normalise the add/edit movie form."""
    title = clean_text(form.get("title"), "Title", 150)
    year = parse_release_year(form.get("release_year"))
    genre = parse_genre(form.get("genre"), allowed_genres)
    poster_url = parse_poster_url(form.get("poster_url"))
    return {
        "title": title,
        "release_year": year,
        "genre": genre,
        "poster_url": poster_url,
    }
