"""Analytics page and server-rendered chart images."""

from flask import Blueprint, Response, abort, render_template

from ..services import analytics, charts

bp = Blueprint("analytics", __name__)


@bp.get("/analytics")
def index():
    stats = analytics.dashboard_stats()
    genre_df = analytics.genre_performance()
    top_rated = analytics.top_rated(limit=10)
    most_rated = analytics.most_rated(limit=10)
    distribution = analytics.rating_distribution()
    best = analytics.best_genre()
    weighted = analytics.add_weighted_scores(analytics.movies_frame())
    weighted_scores = {
        int(row.movie_id): float(row.weighted_score)
        for row in weighted.itertuples()
    } if not weighted.empty else {}

    genre_rows = genre_df.to_dict("records") if not genre_df.empty else []
    top_rows = top_rated.to_dict("records") if not top_rated.empty else []
    most_rows = most_rated.to_dict("records") if not most_rated.empty else []
    for row in top_rows:
        row["weighted_score"] = weighted_scores.get(int(row["movie_id"]), 0.0)
    for row in most_rows:
        row["weighted_score"] = weighted_scores.get(int(row["movie_id"]), 0.0)
    distribution_rows = distribution.to_dict("records")

    chart_cards = [
        {
            "name": "distribution",
            "title": "Rating distribution",
            "subtitle": "Every score from 1 to 10",
            "icon": "bar-chart",
            "tone": "blue",
            "caption": "Counts come directly from the ratings table. Green bars highlight scores of 9 and 10.",
        },
        {
            "name": "genres",
            "title": "Average rating by genre",
            "subtitle": "Which genres score highest",
            "icon": "tags",
            "tone": "mint",
            "caption": "Calculated from individual ratings, not from the average of averages. The leading genre is highlighted.",
        },
        {
            "name": "top-rated",
            "title": "Top-rated movies",
            "subtitle": "Minimum of three ratings",
            "icon": "trophy",
            "tone": "gold",
            "caption": "The rating count in brackets protects the ranking from one-off scores.",
        },
        {
            "name": "rating-counts",
            "title": "Rating volume",
            "subtitle": "Most compared movies",
            "icon": "people",
            "tone": "coral",
            "caption": "Compares how many people rated each movie — useful when judging the confidence of an average.",
        },
    ]

    return render_template(
        "analytics.html",
        active_page="analytics",
        stats=stats,
        genre_rows=genre_rows,
        top_rows=top_rows,
        most_rows=most_rows,
        distribution_rows=distribution_rows,
        best_genre=best,
        chart_cards=chart_cards,
    )


@bp.get("/analytics/chart/<string:name>.svg")
def chart(name):
    if name not in charts.BUILDERS:
        abort(404)
    svg = charts.get_chart(name)
    return Response(
        svg,
        mimetype="image/svg+xml",
        headers={"Cache-Control": "no-store"},
    )
