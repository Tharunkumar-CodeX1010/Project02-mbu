"""Rating queries, including the one-rating-per-user upsert."""

from ..extensions import execute, query_all, query_one


def get_rating(user_id, movie_id):
    return query_one(
        """
        SELECT rating_id, rating, rated_at
        FROM ratings
        WHERE user_id = %s AND movie_id = %s
        """,
        (user_id, movie_id),
    )


def upsert_rating(user_id, movie_id, rating):
    """Insert a rating, or update it when the user already rated the movie."""
    execute(
        """
        INSERT INTO ratings (user_id, movie_id, rating)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            rating = VALUES(rating),
            rated_at = CURRENT_TIMESTAMP
        """,
        (user_id, movie_id, rating),
    )


def list_user_ratings(user_id):
    return query_all(
        """
        SELECT
            r.rating_id,
            r.rating,
            r.rated_at,
            m.movie_id,
            m.title,
            m.release_year,
            m.genre,
            m.poster_url,
            COALESCE(stats.avg_rating, 0) AS avg_rating,
            COALESCE(stats.rating_count, 0) AS rating_count
        FROM ratings r
        JOIN movies m ON m.movie_id = r.movie_id
        LEFT JOIN (
            SELECT movie_id, AVG(rating) AS avg_rating, COUNT(*) AS rating_count
            FROM ratings
            GROUP BY movie_id
        ) stats ON stats.movie_id = m.movie_id
        WHERE r.user_id = %s
        ORDER BY r.rated_at DESC, m.title ASC
        """,
        (user_id,),
    )


def user_rating_summary(user_id):
    row = query_one(
        """
        SELECT
            COUNT(*) AS total,
            ROUND(AVG(rating), 1) AS average_given,
            MAX(rating) AS highest
        FROM ratings
        WHERE user_id = %s
        """,
        (user_id,),
    )
    return {
        "total": int(row["total"]) if row and row["total"] is not None else 0,
        "average_given": row["average_given"] if row else None,
        "highest": row["highest"] if row else None,
    }


def rated_movie_ids(user_id):
    rows = query_all("SELECT movie_id FROM ratings WHERE user_id = %s", (user_id,))
    return {int(row["movie_id"]) for row in rows}


def recent_user_activity(user_id, limit=4):
    """Only the signed-in demo profile's own rating activity.

    The notification panel deliberately avoids other users' rating histories.
    """
    return query_all(
        """
        SELECT
            r.rating,
            r.rated_at,
            u.display_name,
            u.user_id,
            m.movie_id,
            m.title,
            m.poster_url
        FROM ratings r
        JOIN users u ON u.user_id = r.user_id
        JOIN movies m ON m.movie_id = r.movie_id
        WHERE r.user_id = %s
        ORDER BY r.rated_at DESC
        LIMIT %s
        """,
        (user_id, int(limit)),
    )


def total_ratings():
    row = query_one("SELECT COUNT(*) AS total FROM ratings")
    return int(row["total"]) if row else 0


def overall_average():
    row = query_one("SELECT AVG(rating) AS average FROM ratings")
    return float(row["average"]) if row and row["average"] is not None else 0.0


def data_version():
    """Signature used to invalidate generated chart images."""
    row = query_one(
        """
        SELECT
            (SELECT COUNT(*) FROM ratings) AS rating_count,
            (SELECT COALESCE(SUM(rating), 0) FROM ratings) AS rating_sum,
            (SELECT COUNT(*) FROM movies) AS movie_count,
            (SELECT COALESCE(MAX(rated_at), '1970-01-01') FROM ratings) AS latest,
            (SELECT COALESCE(
                SUM(CRC32(CONCAT_WS('|', title, release_year, genre))), 0
             ) FROM movies) AS movie_signature
        """
    )
    if not row:
        return (0, 0, 0, "", 0)
    return (
        row["rating_count"],
        int(row["rating_sum"]),
        row["movie_count"],
        str(row["latest"]),
        int(row["movie_signature"]),
    )


def top_genre_for_user(user_id):
    """The genre this user appreciates most, based on their own ratings."""
    return query_one(
        """
        SELECT m.genre, AVG(r.rating) AS avg_rating, COUNT(*) AS total
        FROM ratings r
        JOIN movies m ON m.movie_id = r.movie_id
        WHERE r.user_id = %s
        GROUP BY m.genre
        ORDER BY avg_rating DESC, total DESC
        LIMIT 1
        """,
        (user_id,),
    )


def highly_rated_for_user(user_id):
    """Movies the user liked most, used as the seed for content similarity."""
    return query_all(
        """
        SELECT
            r.movie_id, r.rating, m.title, m.genre, m.release_year
        FROM ratings r
        JOIN movies m ON m.movie_id = r.movie_id
        WHERE r.user_id = %s AND r.rating >= 8
        ORDER BY r.rating DESC, m.title ASC
        """,
        (user_id,),
    )


def best_rated_by_user(user_id, limit=3):
    """Fallback seeds for users who have not rated anything 8 or above yet."""
    return query_all(
        """
        SELECT
            r.movie_id, r.rating, m.title, m.genre, m.release_year
        FROM ratings r
        JOIN movies m ON m.movie_id = r.movie_id
        WHERE r.user_id = %s
        ORDER BY r.rating DESC, r.rated_at DESC
        LIMIT %s
        """,
        (user_id, int(limit)),
    )
