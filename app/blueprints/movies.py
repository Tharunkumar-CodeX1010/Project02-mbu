"""Catalogue browsing, movie details and the global search API."""

from flask import Blueprint, abort, g, jsonify, render_template, request

from ..repositories import movies as movies_repo
from ..repositories import ratings as ratings_repo
from ..services import recommendations

bp = Blueprint("movies", __name__)


@bp.get("/discover")
def discover():
    search = (request.args.get("q") or "").strip()[:80]
    genre = (request.args.get("genre") or "").strip()
    year = request.args.get("year", type=int)
    sort = request.args.get("sort", "rating")

    genres = movies_repo.list_genres()
    years = movies_repo.list_years()
    if genre not in genres:
        genre = ""
    if year not in years:
        year = None
    if sort not in movies_repo.SORT_OPTIONS:
        sort = "rating"

    results = movies_repo.list_movies(
        search=search or None,
        genre=genre or None,
        year=year,
        sort=sort,
    )

    return render_template(
        "discover.html",
        active_page="discover",
        movies=results,
        genres=genres,
        years=years,
        search=search,
        selected_genre=genre,
        selected_year=year,
        sort=sort,
        sort_options=[
            ("rating", "Highest rating"),
            ("popular", "Most rated"),
            ("year", "Newest release"),
            ("oldest", "Oldest release"),
            ("title", "Title A–Z"),
        ],
    )


@bp.get("/movies/<int:movie_id>")
def detail(movie_id):
    movie = movies_repo.get_movie(movie_id)
    if movie is None:
        abort(404)

    raw_distribution = movies_repo.rating_distribution(movie_id)
    total = sum(raw_distribution.values())
    distribution = []
    for score in range(10, 0, -1):
        count = raw_distribution[score]
        distribution.append(
            {
                "score": score,
                "count": count,
                "percent": round(count / total * 100) if total else 0,
                "bar_width": round(count / max(raw_distribution.values() or [1]) * 100)
                if count
                else 0,
            }
        )

    user = g.get("current_user")
    user_rating = (
        ratings_repo.get_rating(user["user_id"], movie_id) if user else None
    )
    similar = recommendations.similar_to_movie(movie_id, limit=4)

    return render_template(
        "movie_details.html",
        active_page="discover",
        movie=movie,
        distribution=distribution,
        distribution_total=total,
        user_rating=user_rating,
        similar=similar,
    )


@bp.get("/api/search")
def search_api():
    term = (request.args.get("q") or "").strip()
    if len(term) < 2:
        return jsonify([])
    rows = movies_repo.search_titles(term[:80], limit=6)
    return jsonify(
        [
            {
                "id": int(row["movie_id"]),
                "title": row["title"],
                "year": int(row["release_year"]),
                "genre": row["genre"],
            }
            for row in rows
        ]
    )
