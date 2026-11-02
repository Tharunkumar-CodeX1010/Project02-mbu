"""Explainable recommendation algorithms.

Two complementary, easy-to-present approaches are used:

1. Bayesian weighted rating: ranks popular/top-rated movies while accounting
   for how many ratings each movie has.
2. TF-IDF + cosine similarity on movie title and genre: finds movies that are
   textually similar to films the current user rated highly. If scikit-learn is
   unavailable, the function falls back to genre affinity, so the page still
   works.
"""

import numpy as np
from flask import current_app

from ..repositories import movies as movies_repo
from ..repositories import ratings as ratings_repo
from . import analytics


def _record(row, reason, explanation):
    """Convert a DataFrame row to a template-friendly recommendation."""
    return {
        "movie_id": int(row["movie_id"]),
        "title": row["title"],
        "release_year": int(row["release_year"]),
        "genre": row["genre"],
        "poster_url": row["poster_url"],
        "avg_rating": round(float(row["avg_rating"]), 1),
        "rating_count": int(row["rating_count"]),
        "weighted_score": round(float(row.get("weighted_score", 0.0)), 1),
        "reason": reason,
        "explanation": explanation,
    }


def _ranked_frame(user_id=None):
    frame = analytics.add_weighted_scores(analytics.movies_frame())
    if user_id is not None and not frame.empty:
        rated = ratings_repo.rated_movie_ids(user_id)
        frame = frame[~frame["movie_id"].isin(rated)].copy()
    return frame


def popular(user_id=None, limit=None):
    """Bayesian popularity: quality and rating volume in one score."""
    limit = limit or current_app.config["RECOMMENDATION_LIMIT"]
    frame = _ranked_frame(user_id)
    if frame.empty:
        return []
    frame = frame[frame["rating_count"] > 0].head(limit)
    return [
        _record(
            row,
            "Popular",
            (
                f"Popular with {int(row['rating_count'])} ratings and a "
                f"weighted score of {float(row['weighted_score']):.1f}/10 — "
                "the score balances quality with how many people rated it."
            ),
        )
        for row in frame.to_dict("records")
    ]


def top_rated(user_id=None, limit=None):
    """Highest averages, with a minimum rating count to avoid tiny samples."""
    limit = limit or current_app.config["RECOMMENDATION_LIMIT"]
    minimum = current_app.config["TOP_RATED_MIN_COUNT"]
    frame = _ranked_frame(user_id)
    if frame.empty:
        return []
    qualified = frame[frame["rating_count"] >= minimum]
    if qualified.empty:
        qualified = frame[frame["rating_count"] > 0]
    qualified = qualified.sort_values(
        ["avg_rating", "rating_count"], ascending=[False, False]
    ).head(limit)
    return [
        _record(
            row,
            "Top rated",
            (
                f"Recommended because it has a high average rating of "
                f"{float(row['avg_rating']):.1f}/10 from "
                f"{int(row['rating_count'])} ratings."
            ),
        )
        for row in qualified.to_dict("records")
    ]


def genre_recommendations(user_id, genre=None, limit=None):
    """Genre affinity picks, preferring the user's best-loved genre."""
    limit = limit or current_app.config["RECOMMENDATION_LIMIT"]
    available = movies_repo.list_genres()
    frame = _ranked_frame(user_id)

    auto_selected = False
    if genre not in available:
        preference = ratings_repo.top_genre_for_user(user_id)
        if preference:
            genre = preference["genre"]
            auto_selected = True
        elif available:
            genre = "Sci-Fi" if "Sci-Fi" in available else available[0]
            auto_selected = True

    if not genre or frame.empty:
        return {"genre": genre, "auto_selected": auto_selected, "movies": []}

    matches = frame[frame["genre"] == genre].sort_values(
        ["weighted_score", "avg_rating"], ascending=[False, False]
    ).head(limit)

    items = []
    for row in matches.to_dict("records"):
        if auto_selected:
            explanation = (
                f"Recommended because {genre} is the genre you rate highest, "
                f"and this film averages {float(row['avg_rating']):.1f}/10."
            )
        else:
            explanation = (
                f"Recommended because it matches your selected genre "
                f"({genre}) and averages {float(row['avg_rating']):.1f}/10 "
                f"from {int(row['rating_count'])} ratings."
            )
        items.append(_record(row, "Genre match", explanation))

    return {"genre": genre, "auto_selected": auto_selected, "movies": items}


def _similarity_matrix(frame):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    # Repeating the genre gives it more weight than a single title token.
    corpus = [
        f"{row.title} {row.genre} {row.genre}" for row in frame.itertuples()
    ]
    vectorizer = TfidfVectorizer(
        stop_words="english", ngram_range=(1, 2), sublinear_tf=True
    )
    matrix = vectorizer.fit_transform(corpus)
    return matrix, cosine_similarity(matrix)


def for_you(user_id, limit=None):
    """Content-based picks seeded by the movies this user rated highly."""
    limit = limit or current_app.config["RECOMMENDATION_LIMIT"]
    frame = _ranked_frame()
    if frame.empty:
        return []

    seeds = ratings_repo.highly_rated_for_user(user_id)
    if not seeds:
        seeds = ratings_repo.best_rated_by_user(user_id, limit=3)
    if not seeds:
        return []

    available = {int(row["movie_id"]): row for row in frame.to_dict("records")}
    seed_rows = [seed for seed in seeds if int(seed["movie_id"]) in available]
    if not seed_rows:
        return []

    try:
        matrix, _similarity = _similarity_matrix(frame)
        index_of = {
            int(movie_id): position
            for position, movie_id in enumerate(frame["movie_id"].tolist())
        }
        seed_positions = [index_of[int(seed["movie_id"])] for seed in seed_rows]
        seed_vector = np.asarray(matrix[seed_positions].mean(axis=0)).ravel()
        from sklearn.metrics.pairwise import cosine_similarity

        scores = cosine_similarity(seed_vector.reshape(1, -1), matrix).ravel()
    except (ImportError, ValueError):
        # Graceful fallback: use the user's genre preference instead.
        preference = ratings_repo.top_genre_for_user(user_id)
        if not preference:
            return []
        fallback = frame[frame["genre"] == preference["genre"]].head(limit)
        return [
            _record(
                row,
                "For you",
                f"Because you enjoy {preference['genre']} films and this one "
                f"averages {float(row['avg_rating']):.1f}/10.",
            )
            for row in fallback.to_dict("records")
        ]

    rated = ratings_repo.rated_movie_ids(user_id)
    candidates = []
    seed_similarity = None
    if seed_positions:
        # Similarity of every movie to each seed, so we can name the reason.
        seed_similarity = (matrix[seed_positions] @ matrix.T).toarray()

    for position, row in enumerate(frame.to_dict("records")):
        if int(row["movie_id"]) in rated:
            continue
        score = float(scores[position])
        if score <= 0.001:
            continue
        seed_position = 0
        if seed_similarity is not None and len(seed_positions) > 1:
            seed_position = int(np.argmax(seed_similarity[:, position]))
        seed = seed_rows[seed_position]
        candidates.append((score, row, seed))

    candidates.sort(key=lambda item: (-item[0], -item[1]["weighted_score"]))
    items = []
    for score, row, seed in candidates[:limit]:
        explanation = (
            f"Because you rated {seed['title']} {int(seed['rating'])}/10 and "
            f"both are {seed['genre']} films with a similar tone."
        )
        items.append(_record(row, "For you", explanation))
    return items


def similar_to_movie(movie_id, limit=4):
    """Content similarity used on the movie details page."""
    frame = analytics.add_weighted_scores(analytics.movies_frame())
    if frame.empty or len(frame) < 2:
        return []

    target = frame[frame["movie_id"] == movie_id]
    if target.empty:
        return []
    target_title = target.iloc[0]["title"]
    target_genre = target.iloc[0]["genre"]

    try:
        matrix, similarity = _similarity_matrix(frame)
        index_of = {
            int(mid): position for position, mid in enumerate(frame["movie_id"].tolist())
        }
        target_position = index_of[int(movie_id)]
        scores = similarity[target_position]
    except (ImportError, ValueError):
        scores = np.zeros(len(frame))

    candidates = []
    for position, row in enumerate(frame.to_dict("records")):
        if int(row["movie_id"]) == int(movie_id):
            continue
        score = float(scores[position])
        if score > 0:
            candidates.append((score, row))

    candidates.sort(key=lambda item: (-item[0], -item[1]["weighted_score"]))
    if not candidates:
        fallback = frame[
            (frame["genre"] == target_genre)
            & (frame["movie_id"] != int(movie_id))
        ].head(limit)
        return [
            _record(
                row,
                "Similar",
                f"Shares the {target_genre} genre with {target_title}.",
            )
            for row in fallback.to_dict("records")
        ]

    items = []
    for _score, row in candidates[:limit]:
        explanation = (
            f"Shares its {row['genre']} style with {target_title} and averages "
            f"{float(row['avg_rating']):.1f}/10."
        )
        items.append(_record(row, "Similar", explanation))
    return items
