"""User queries (the prototype uses seeded demo accounts instead of logins)."""

from ..extensions import query_all, query_one


def get_user(user_id):
    return query_one(
        "SELECT user_id, display_name FROM users WHERE user_id = %s",
        (user_id,),
    )


def list_users():
    return query_all(
        "SELECT user_id, display_name FROM users ORDER BY display_name ASC"
    )


def count_users():
    row = query_one("SELECT COUNT(*) AS total FROM users")
    return int(row["total"]) if row else 0
