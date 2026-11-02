"""Pandas/NumPy analysis for the dashboard and analytics pages.

The analysis layer only reads aggregated data from the repositories; SQL stays
in the repository layer and presentation stays in the templates.
"""

import numpy as np
import pandas as pd
from flask import current_app

from ..extensions import query_all
from ..repositories import movies as movies_repo
from ..repositories import ratings as ratings_repo
from ..repositories import users as users_repo

MOVIE_COLUMNS = [
    "movie_id",
    "title",
    "release_year",
    "genre",
    "poster_url",
    "avg_rating",
    "rating_count",
]


def movies_frame():
    """Load every movie with its aggregate rating into a typed DataFrame."""
    rows = movies_repo.get_all_with_stats()
    df = pd.DataFrame(rows, columns=MOVIE_COLUMNS)
    if df.empty:
        return df

    df["movie_id"] = df["movie_id"].astype(int)
    df["release_year"] = df["release_year"].astype(int)
    df["avg_rating"] = pd.to_numeric(df["avg_rating"], errors="coerce").fillna(0.0)
    df["rating_count"] = (
        pd.to_numeric(df["rating_count"], errors="coerce").fillna(0).astype(int)
    )
    return df


def weighted_rating(row_or_series, mean_rating, min_count):
    """Bayesian weighted rating.

    WR = (v / (v + m)) * R + (m / (v + m)) * C
    where R is the movie average, v its rating count, m the minimum count
    threshold and C the overall catalogue average.
    """
    v = float(row_or_series["rating_count"])
    r = float(row_or_series["avg_rating"])
    m = float(min_count)
    c = float(mean_rating)
    return (v / (v + m)) * r + (m / (v + m)) * c


def add_weighted_scores(df, min_count=None, mean_rating=None):
    """Vectorised Bayesian scores plus a human-readable rank position."""
    min_count = current_app.config["MIN_RATING_COUNT"] if min_count is None else min_count
    mean_rating = ratings_repo.overall_average() if mean_rating is None else mean_rating

    result = df.copy()
    if result.empty:
        result["weighted_score"] = []
        result["overall_mean"] = []
        return result

    v = result["rating_count"].astype(float)
    r = result["avg_rating"].astype(float)
    m = float(min_count)
    c = float(mean_rating or 0.0)

    result["weighted_score"] = np.where(
        v > 0,
        (v / (v + m)) * r + (m / (v + m)) * c,
        0.0,
    )
    result["weighted_score"] = result["weighted_score"].round(2)
    result["overall_mean"] = round(c, 2)
    result = result.sort_values(
        ["weighted_score", "rating_count", "avg_rating"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    result["rank"] = np.arange(1, len(result) + 1)
    return result


def dashboard_stats():
    """Headline numbers shown on the dashboard."""
    df = movies_frame()
    return {
        "total_movies": int(len(df)),
        "total_ratings": ratings_repo.total_ratings(),
        "average_rating": round(ratings_repo.overall_average(), 2),
        "total_users": users_repo.count_users(),
        "total_genres": int(df["genre"].nunique()) if not df.empty else 0,
    }


def genre_performance():
    """Actual average rating per genre (one row per rating), with movie counts."""
    rows = query_all(
        """
        SELECT
            m.genre,
            ROUND(AVG(r.rating), 2) AS avg_rating,
            COUNT(r.rating_id) AS rating_count,
            COUNT(DISTINCT m.movie_id) AS movie_count
        FROM movies m
        JOIN ratings r ON r.movie_id = m.movie_id
        GROUP BY m.genre
        ORDER BY avg_rating DESC, rating_count DESC
        """
    )
    df = pd.DataFrame(
        rows, columns=["genre", "avg_rating", "rating_count", "movie_count"]
    )
    if df.empty:
        return df
    df["avg_rating"] = pd.to_numeric(df["avg_rating"])
    df["rating_count"] = df["rating_count"].astype(int)
    df["movie_count"] = df["movie_count"].astype(int)
    return df


def rating_distribution():
    """Counts for scores 1-10 across the whole database (zero-filled)."""
    rows = query_all(
        """
        SELECT rating, COUNT(*) AS total
        FROM ratings
        GROUP BY rating
        """
    )
    counts = {score: 0 for score in range(1, 11)}
    for row in rows:
        counts[int(row["rating"])] = int(row["total"])
    df = pd.DataFrame(
        {"score": list(counts.keys()), "count": list(counts.values())}
    )
    total = int(df["count"].sum())
    df["share"] = (df["count"] / total * 100).round(1) if total else 0.0
    return df


def top_rated(limit=10, min_count=None):
    """Highest averages, with a small minimum to avoid one-rating outliers."""
    min_count = (
        current_app.config["TOP_RATED_MIN_COUNT"] if min_count is None else min_count
    )
    df = movies_frame()
    if df.empty:
        return df
    ranked = df[df["rating_count"] >= min_count].copy()
    if ranked.empty:
        ranked = df[df["rating_count"] > 0].copy()
    ranked = ranked.sort_values(
        ["avg_rating", "rating_count"], ascending=[False, False]
    ).head(limit)
    return ranked.reset_index(drop=True)


def most_rated(limit=10):
    df = movies_frame()
    if df.empty:
        return df
    ranked = df[df["rating_count"] > 0].sort_values(
        ["rating_count", "avg_rating"], ascending=[False, False]
    ).head(limit)
    return ranked.reset_index(drop=True)


def best_genre():
    df = genre_performance()
    if df.empty:
        return None
    row = df.iloc[0]
    return {
        "genre": row["genre"],
        "avg_rating": float(row["avg_rating"]),
        "rating_count": int(row["rating_count"]),
    }
