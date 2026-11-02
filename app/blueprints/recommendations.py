"""Recommendation page."""

from flask import Blueprint, g, render_template, request

from ..repositories import movies as movies_repo
from ..repositories import ratings as ratings_repo
from ..services import recommendations

bp = Blueprint("recommendations", __name__)


@bp.get("/recommendations")
def index():
    user = g.get("current_user")
    user_id = user["user_id"] if user else None

    selected_genre = (request.args.get("genre") or "").strip()
    genres = movies_repo.list_genres()
    if selected_genre not in genres:
        selected_genre = None

    genre_result = recommendations.genre_recommendations(
        user_id, genre=selected_genre
    )
    summary = ratings_repo.user_rating_summary(user_id) if user_id else None

    return render_template(
        "recommendations.html",
        active_page="recommendations",
        genres=genres,
        selected_genre=selected_genre,
        genre_result=genre_result,
        for_you=recommendations.for_you(user_id),
        popular=recommendations.popular(user_id),
        top_rated=recommendations.top_rated(user_id),
        summary=summary,
    )
