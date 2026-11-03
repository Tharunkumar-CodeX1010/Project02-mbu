"""MovieScope Flask application factory."""

from datetime import date

import pymysql
from flask import Flask, g, render_template, request, session

from config import Config

from .extensions import init_app as init_database
from .posters import poster_source
from .repositories import movies as movies_repo
from .repositories import ratings as ratings_repo
from .repositories import users as users_repo


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    init_database(app)

    # Blueprints keep pages, API endpoints and admin actions separated.
    from .blueprints.analytics import bp as analytics_bp
    from .blueprints.dashboard import bp as dashboard_bp
    from .blueprints.manage import bp as manage_bp
    from .blueprints.movies import bp as movies_bp
    from .blueprints.ratings import bp as ratings_bp
    from .blueprints.recommendations import bp as recommendations_bp
    from .blueprints.users import bp as users_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(movies_bp)
    app.register_blueprint(ratings_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(manage_bp)
    app.register_blueprint(users_bp)

    @app.before_request
    def load_current_user():
        """The academic prototype uses a seeded demo user, not a login form."""
        if request.endpoint == "static":
            return
        user_id = session.get("user_id", app.config["DEMO_USER_ID"])
        user = users_repo.get_user(user_id)
        if user is None:
            available = users_repo.list_users()
            user = available[0] if available else None
            if user is not None:
                session["user_id"] = user["user_id"]
        g.current_user = user

    @app.context_processor
    def inject_layout_data():
        data = {
            "current_user": g.get("current_user"),
            "all_genres": [],
            "nav_users": [],
            "recent_activity": [],
            "current_year": date.today().year,
        }
        try:
            data["all_genres"] = movies_repo.list_genres()
            data["nav_users"] = users_repo.list_users()
            current = g.get("current_user")
            if current:
                data["recent_activity"] = ratings_repo.recent_user_activity(
                    current["user_id"], 4
                )
        except pymysql.MySQLError:
            # The error page still needs to render when MySQL is unavailable.
            pass
        return data

    app.jinja_env.globals["poster_source"] = poster_source

    @app.template_filter("rating")
    def format_rating(value, fallback="—"):
        try:
            return f"{float(value):.1f}"
        except (TypeError, ValueError):
            return fallback

    @app.template_filter("datefmt")
    def format_date(value, pattern="%d %b %Y"):
        try:
            return value.strftime(pattern)
        except AttributeError:
            return "—"

    @app.template_filter("initials")
    def initials(name):
        parts = [part for part in (name or "").split() if part]
        return "".join(part[0].upper() for part in parts[:2]) or "MS"

    @app.errorhandler(404)
    def not_found(_error):
        return (
            render_template(
                "error.html",
                code=404,
                title="Page not found",
                message="The page you are looking for may have moved or no longer exists.",
                show_setup=False,
            ),
            404,
        )

    @app.errorhandler(500)
    def server_error(_error):
        return (
            render_template(
                "error.html",
                code=500,
                title="Something went wrong",
                message="An unexpected error occurred. Please try again.",
                show_setup=False,
            ),
            500,
        )

    @app.errorhandler(pymysql.MySQLError)
    def database_error(error):
        app.logger.error("Database error: %s", error)
        return (
            render_template(
                "error.html",
                code=503,
                title="Database unavailable",
                message=(
                    "MovieScope could not reach MySQL. Make sure the database is "
                    "running, then check your .env settings and initialise the data."
                ),
                show_setup=True,
                db_host=app.config["DB_HOST"],
                db_port=app.config["DB_PORT"],
                db_name=app.config["DB_NAME"],
                db_user=app.config["DB_USER"],
            ),
            503,
        )

    return app
