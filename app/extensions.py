"""Small database helpers shared by the repositories.

A new PyMySQL connection is opened per request and closed automatically when
the request ends. All callers receive dictionary rows, which keeps templates
and the Pandas layer simple to work with.
"""

import pymysql
from flask import current_app, g
from pymysql.cursors import DictCursor


def get_db():
    """Return (and lazily create) the connection for the current request."""
    if "db" not in g:
        g.db = pymysql.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            database=current_app.config["DB_NAME"],
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
            connect_timeout=5,
        )
    return g.db


def close_db(_exception=None):
    """Close the request-scoped connection, if one was opened."""
    db = g.pop("db", None)
    if db is not None:
        try:
            db.close()
        except Exception:  # pragma: no cover - defensive cleanup
            pass


def init_app(app):
    app.teardown_appcontext(close_db)


def query_all(sql, params=None):
    with get_db().cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchall()


def query_one(sql, params=None):
    with get_db().cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchone()


def execute(sql, params=None):
    """Run a write statement and commit it. Returns lastrowid."""
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(sql, params or ())
        row_id = cursor.lastrowid
    db.commit()
    return row_id
