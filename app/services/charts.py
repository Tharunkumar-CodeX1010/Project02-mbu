"""Matplotlib chart rendering.

Charts are rendered server-side to SVG so they stay crisp on large screens
and work without a charting JavaScript library. Results are cached until the
underlying ratings/movies change.
"""

from io import BytesIO
import os

import matplotlib

if os.getenv("VERCEL") == "1":
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (must follow backend selection)

from ..repositories import ratings as ratings_repo  # noqa: E402
from . import analytics  # noqa: E402

INK = "#123B46"
MUTED = "#71828B"
GRID = "#EDF2F3"
BORDER = "#E5ECEE"
BLUE = "#3978CE"
GREEN = "#087F69"
GOLD = "#D78B16"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "text.color": INK,
        "axes.labelcolor": MUTED,
        "axes.edgecolor": BORDER,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 1,
    }
)


def _new_figure(width=6.6, height=3.3):
    fig, ax = plt.subplots(figsize=(width, height), dpi=150)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(BORDER)
    ax.tick_params(length=0)
    ax.set_axisbelow(True)
    return fig, ax


def _to_svg(fig):
    buffer = BytesIO()
    fig.savefig(
        buffer,
        format="svg",
        bbox_inches="tight",
        pad_inches=0.22,
        facecolor="#FFFFFF",
    )
    plt.close(fig)
    buffer.seek(0)
    return buffer.getvalue()


def _distribution_chart():
    df = analytics.rating_distribution()
    fig, ax = _new_figure(6.6, 3.2)
    colors = [GREEN if score >= 9 else BLUE for score in df["score"]]
    bars = ax.bar(df["score"].astype(str), df["count"], color=colors, width=0.64)
    ax.set_xlabel("Rating score (1–10)")
    ax.set_ylabel("Number of ratings")
    ax.grid(axis="x", visible=False)
    max_count = max(int(df["count"].max()), 1)
    ax.set_ylim(0, max_count * 1.22)
    for bar, count in zip(bars, df["count"]):
        if count:
            ax.annotate(
                str(int(count)),
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                ha="center",
                va="bottom",
                fontsize=8,
                color=INK,
            )
    return _to_svg(fig)


def _genre_chart():
    df = analytics.genre_performance()
    fig, ax = _new_figure(6.6, 3.4)
    if df.empty:
        ax.text(0.5, 0.5, "No genre data yet", ha="center", va="center")
        return _to_svg(fig)

    data = df.sort_values("avg_rating", ascending=True)
    colors = [GREEN if i == len(data) - 1 else BLUE for i in range(len(data))]
    bars = ax.barh(data["genre"], data["avg_rating"], color=colors, height=0.62)
    ax.set_xlim(0, 10)
    ax.set_xlabel("Average rating")
    ax.set_ylabel("")
    ax.grid(axis="y", visible=False)
    for bar, value in zip(bars, data["avg_rating"]):
        ax.annotate(
            f"{float(value):.1f}",
            (bar.get_width() + 0.12, bar.get_y() + bar.get_height() / 2),
            va="center",
            fontsize=8,
            color=INK,
        )
    return _to_svg(fig)


def _top_rated_chart():
    df = analytics.top_rated(limit=8)
    fig, ax = _new_figure(6.6, 3.6)
    if df.empty:
        ax.text(0.5, 0.5, "No ratings yet", ha="center", va="center")
        return _to_svg(fig)

    data = df.sort_values("avg_rating", ascending=True)
    labels = [
        f"{title[:26]}…" if len(title) > 27 else title
        for title in data["title"].tolist()
    ]
    colors = [GREEN if i == len(data) - 1 else BLUE for i in range(len(data))]
    bars = ax.barh(labels, data["avg_rating"], color=colors, height=0.62)
    ax.set_xlim(0, 10)
    ax.set_xlabel("Average rating")
    ax.grid(axis="y", visible=False)
    for bar, row in zip(bars, data.itertuples()):
        ax.annotate(
            f"{float(row.avg_rating):.1f} ({int(row.rating_count)})",
            (bar.get_width() + 0.12, bar.get_y() + bar.get_height() / 2),
            va="center",
            fontsize=7.5,
            color=INK,
        )
    return _to_svg(fig)


def _rating_count_chart():
    df = analytics.most_rated(limit=10)
    fig, ax = _new_figure(6.6, 3.6)
    if df.empty:
        ax.text(0.5, 0.5, "No ratings yet", ha="center", va="center")
        return _to_svg(fig)

    data = df.sort_values("rating_count", ascending=True)
    labels = [
        f"{title[:26]}…" if len(title) > 27 else title
        for title in data["title"].tolist()
    ]
    bars = ax.barh(labels, data["rating_count"], color=GOLD, height=0.62)
    ax.set_xlabel("Number of ratings")
    ax.grid(axis="y", visible=False)
    for bar, value in zip(bars, data["rating_count"]):
        ax.annotate(
            str(int(value)),
            (bar.get_width() + 0.12, bar.get_y() + bar.get_height() / 2),
            va="center",
            fontsize=8,
            color=INK,
        )
    return _to_svg(fig)


BUILDERS = {
    "distribution": _distribution_chart,
    "genres": _genre_chart,
    "top-rated": _top_rated_chart,
    "rating-counts": _rating_count_chart,
}

_cache = {}


def get_chart(name):
    """Return SVG bytes for a chart, rebuilding only when data changes."""
    builder = BUILDERS.get(name)
    if builder is None:
        raise KeyError(f"Unknown chart: {name}")

    version = ratings_repo.data_version()
    key = (name, version)
    if key not in _cache:
        if len(_cache) > 32:
            _cache.clear()
        _cache[key] = builder()
    return _cache[key]
