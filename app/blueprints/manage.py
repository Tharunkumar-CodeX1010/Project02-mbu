"""Movie catalogue administration (add, edit, delete)."""

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from ..repositories import movies as movies_repo
from ..utils.validators import ValidationError, parse_movie_form

bp = Blueprint("manage", __name__)


@bp.get("/manage")
def index():
    search = (request.args.get("q") or "").strip()[:80]
    rows = movies_repo.list_movies(search=search or None, sort="title")
    return render_template(
        "manage_movies.html",
        active_page="manage",
        movies=rows,
        search=search,
        genres=current_app.config["GENRES"],
    )


@bp.post("/manage/add")
def add_movie():
    try:
        data = parse_movie_form(request.form, current_app.config["GENRES"])
    except ValidationError as error:
        flash(str(error), "danger")
        return redirect(url_for("manage.index"))

    movies_repo.create_movie(data)
    flash(f"“{data['title']}” was added to the catalogue.", "success")
    return redirect(url_for("manage.index"))


@bp.post("/manage/<int:movie_id>/edit")
def edit_movie(movie_id):
    movie = movies_repo.get_movie(movie_id)
    if movie is None:
        flash("That movie could not be found.", "danger")
        return redirect(url_for("manage.index"))

    try:
        data = parse_movie_form(request.form, current_app.config["GENRES"])
    except ValidationError as error:
        flash(str(error), "danger")
        return redirect(url_for("manage.index"))

    movies_repo.update_movie(movie_id, data)
    flash(f"“{data['title']}” was updated.", "success")
    return redirect(url_for("manage.index"))


@bp.post("/manage/<int:movie_id>/delete")
def delete_movie(movie_id):
    movie = movies_repo.get_movie(movie_id)
    if movie is None:
        flash("That movie could not be found.", "danger")
        return redirect(url_for("manage.index"))

    movies_repo.delete_movie(movie_id)
    flash(f"“{movie['title']}” was deleted along with its ratings.", "success")
    return redirect(url_for("manage.index"))
