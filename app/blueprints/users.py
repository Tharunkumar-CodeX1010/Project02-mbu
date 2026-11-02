"""Demo profile switching.

The project intentionally avoids a full authentication system; instead, the
seeded users can be switched from the header to demonstrate per-user ratings.
"""

from flask import Blueprint, flash, redirect, request, session, url_for

from ..repositories import users as users_repo

bp = Blueprint("users", __name__)


@bp.post("/switch-user/<int:user_id>")
def switch_user(user_id):
    user = users_repo.get_user(user_id)
    if user is None:
        flash("That demo profile does not exist.", "danger")
    else:
        session["user_id"] = user["user_id"]
        flash(f"Switched to {user['display_name']}.", "info")

    next_url = request.form.get("next") or ""
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = url_for("dashboard.index")
    return redirect(next_url)
