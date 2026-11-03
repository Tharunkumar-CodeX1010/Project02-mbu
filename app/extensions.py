"""Small PostgreSQL helpers shared by the repositories.

A new psycopg connection is opened per request and closed automatically when
the request ends. All callers receive dictionary rows, which keeps templates
and the Pandas layer simple to work with.
"""

import psycopg
from flask import current_app, g
from psycopg.rows import dict_row


def get_db():
    """Return (and lazily create) the connection for the current request."""
    if "db" not in g:
        g.db = psycopg.connect(
            current_app.config["DATABASE_URL"],
            row_factory=dict_row,
            autocommit=False,
            connect_timeout=5,
            prepare_threshold=None,
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
    """Run a write statement and commit it, returning a requested id if present."""
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(sql, params or ())
        row = cursor.fetchone() if cursor.description else None
    db.commit()
    return next(iter(row.values())) if row else None
