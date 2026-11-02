"""Dashboard page."""

from flask import Blueprint, g, render_template

from ..repositories import ratings as ratings_repo
from ..services import analytics

bp = Blueprint("dashboard", __name__)


@bp.get("/")
def index():
    stats = analytics.dashboard_stats()

    ranked = analytics.add_weighted_scores(analytics.movies_frame())
    featured = ranked.head(4).to_dict("records") if not ranked.empty else []

    genre_df = analytics.genre_performance()
    preview = []
    for row in genre_df.head(5).to_dict("records"):
        preview.append(
            {
                "genre": row["genre"],
                "avg_rating": float(row["avg_rating"]),
                "rating_count": int(row["rating_count"]),
                "width": max(4.0, min(100.0, float(row["avg_rating"]) * 10)),
            }
        )

    user = g.get("current_user")
    user_summary = (
        ratings_repo.user_rating_summary(user["user_id"]) if user else None
    )
    latest_ratings = (
        ratings_repo.list_user_ratings(user["user_id"])[:3] if user else []
    )
    best = analytics.best_genre()

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        stats=stats,
        featured=featured,
        genre_preview=preview,
        best_genre=best,
        user_summary=user_summary,
        latest_ratings=latest_ratings,
    )
