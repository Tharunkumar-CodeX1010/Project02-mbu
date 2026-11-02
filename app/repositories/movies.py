"""Movie catalogue queries.

Every statement uses placeholders; sort options are mapped through a fixed
allow-list instead of being interpolated from user input.
"""

from ..extensions import execute, query_all, query_one

BASE_SELECT = """
    SELECT
        m.movie_id,
        m.title,
        m.release_year,
        m.genre,
        m.poster_url,
        ROUND(COALESCE(AVG(r.rating), 0), 2) AS avg_rating,
        COUNT(r.rating_id) AS rating_count
    FROM movies m
    LEFT JOIN ratings r ON r.movie_id = m.movie_id
"""

SORT_OPTIONS = {
    "rating": "avg_rating DESC, rating_count DESC, m.title ASC",
    "year": "m.release_year DESC, m.title ASC",
    "title": "m.title ASC",
    "popular": "rating_count DESC, avg_rating DESC, m.title ASC",
    "oldest": "m.release_year ASC, m.title ASC",
}


def list_movies(search=None, genre=None, year=None, sort="rating", limit=None):
    """Return catalogue rows with aggregate rating information.

    All filters are optional and compose with each other and with sorting.
    """
    where = []
    params = []

    if search:
        where.append("m.title LIKE %s")
        params.append(f"%{search}%")
    if genre:
        where.append("m.genre = %s")
        params.append(genre)
    if year:
        where.append("m.release_year = %s")
        params.append(year)

    sql = BASE_SELECT
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " GROUP BY m.movie_id, m.title, m.release_year, m.genre, m.poster_url"
    sql += " ORDER BY " + SORT_OPTIONS.get(sort, SORT_OPTIONS["rating"])

    if limit is not None:
        sql += " LIMIT %s"
        params.append(int(limit))

    return query_all(sql, tuple(params))


def get_movie(movie_id):
    sql = BASE_SELECT + """
        WHERE m.movie_id = %s
        GROUP BY m.movie_id, m.title, m.release_year, m.genre, m.poster_url
    """
    return query_one(sql, (movie_id,))


def get_all_with_stats():
    """Used by the Pandas analytics and recommendation layers."""
    return list_movies(sort="rating")


def create_movie(data):
    return execute(
        """
        INSERT INTO movies (title, release_year, genre, poster_url)
        VALUES (%s, %s, %s, %s)
        """,
        (data["title"], data["release_year"], data["genre"], data["poster_url"]),
    )


def update_movie(movie_id, data):
    execute(
        """
        UPDATE movies
        SET title = %s, release_year = %s, genre = %s, poster_url = %s
        WHERE movie_id = %s
        """,
        (
            data["title"],
            data["release_year"],
            data["genre"],
            data["poster_url"],
            movie_id,
        ),
    )


def delete_movie(movie_id):
    execute("DELETE FROM movies WHERE movie_id = %s", (movie_id,))


def list_genres():
    rows = query_all("SELECT DISTINCT genre FROM movies ORDER BY genre")
    return [row["genre"] for row in rows]


def list_years():
    rows = query_all(
        "SELECT DISTINCT release_year FROM movies ORDER BY release_year DESC"
    )
    return [row["release_year"] for row in rows]


def search_titles(term, limit=5):
    return query_all(
        """
        SELECT movie_id, title, release_year, genre, poster_url
        FROM movies
        WHERE title LIKE %s
        ORDER BY title ASC
        LIMIT %s
        """,
        (f"%{term}%", int(limit)),
    )


def rating_distribution(movie_id):
    """Return counts for every score from 1 to 10 (zero-filled)."""
    rows = query_all(
        """
        SELECT rating, COUNT(*) AS total
        FROM ratings
        WHERE movie_id = %s
        GROUP BY rating
        """,
        (movie_id,),
    )
    counts = {score: 0 for score in range(1, 11)}
    for row in rows:
        counts[int(row["rating"])] = int(row["total"])
    return counts
