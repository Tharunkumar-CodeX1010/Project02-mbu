"""Rating submission and the current user's rating history."""

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from ..repositories import movies as movies_repo
from ..repositories import ratings as ratings_repo
from ..utils.validators import ValidationError, parse_rating

bp = Blueprint("ratings", __name__)


def _current_user_id():
    user = g.get("current_user")
    if user is None:
        abort(404)
    return user["user_id"]


@bp.post("/movies/<int:movie_id>/rate")
def rate_movie(movie_id):
    movie = movies_repo.get_movie(movie_id)
    if movie is None:
        abort(404)

    try:
        rating = parse_rating(request.form.get("rating"))
    except ValidationError as error:
        flash(str(error), "danger")
        return redirect(url_for("movies.detail", movie_id=movie_id) + "#rate")

    existing = ratings_repo.get_rating(_current_user_id(), movie_id)
    ratings_repo.upsert_rating(_current_user_id(), movie_id, rating)

    if existing:
        flash(
            f"Your rating for {movie['title']} was updated to {rating}/10.",
            "success",
        )
    else:
        flash(f"Thanks! You rated {movie['title']} {rating}/10.", "success")
    return redirect(url_for("movies.detail", movie_id=movie_id) + "#ratings")


@bp.get("/my-ratings")
def my_ratings():
    user_id = _current_user_id()
    rows = ratings_repo.list_user_ratings(user_id)
    summary = ratings_repo.user_rating_summary(user_id)
    return render_template(
        "my_ratings.html",
        active_page="ratings",
        ratings=rows,
        summary=summary,
    )


@bp.post("/my-ratings/update")
def update_rating():
    user_id = _current_user_id()
    movie_id = request.form.get("movie_id", type=int)
    if not movie_id:
        flash("Please choose a movie to update.", "danger")
        return redirect(url_for("ratings.my_ratings"))

    existing = ratings_repo.get_rating(user_id, movie_id)
    if existing is None:
        flash("That rating could not be found for your account.", "danger")
        return redirect(url_for("ratings.my_ratings"))

    try:
        rating = parse_rating(request.form.get("rating"))
    except ValidationError as error:
        flash(str(error), "danger")
        return redirect(url_for("ratings.my_ratings"))

    ratings_repo.upsert_rating(user_id, movie_id, rating)
    flash("Your rating was updated.", "success")
    return redirect(url_for("ratings.my_ratings"))
