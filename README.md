# MovieScope

**Every movie has a story.**

MovieScope is a college-level, full-stack movie discovery, ratings and analytics prototype. It combines a curated PostgreSQL catalogue with a Flask backend, Pandas/NumPy analysis, Matplotlib charts and explainable recommendations.

The project is designed to be demonstrated live: it ships with 60 films, 15 demo profiles and 230 ratings, so every chart, ranking and recommendation is populated immediately after setup.

---

## 1. What it does

MovieScope has seven connected pages:

| Page | What you can do |
| --- | --- |
| **Dashboard** (`/`) | See live totals, featured movies, a genre analytics preview, your taste snapshot and quick actions. |
| **Discover Movies** (`/discover`) | Search by title, filter by genre and release year, and sort by rating, popularity, year or title. All controls combine. |
| **Movie Details** (`/movies/<id>`) | View poster, metadata, community average, rating count, a 1–10 distribution and similar movies. Submit or update a rating. |
| **Recommendations** (`/recommendations`) | Get content-based personal picks, Bayesian-popular picks, top-rated films and genre suggestions — each with a written explanation. |
| **Analytics** (`/analytics`) | Explore four Matplotlib charts plus leaderboards calculated from live PostgreSQL data. |
| **Manage Movies** (`/manage`) | Search, add, edit and delete catalogue entries with validation and a confirmation dialog before deletion. |
| **My Ratings** (`/my-ratings`) | Review and update only the current demo profile's ratings. |

The header also includes working global search with suggestions, a private recent-activity panel for the current profile, and a demo profile switcher.

### Core behaviour

- One rating per user per movie, enforced by a database unique key.
- Submitting a rating again updates it instead of creating a duplicate.
- Ratings are validated in the browser (radio input required) and on the server (integer 1–10).
- Deleting a movie cascades to its ratings, after explicit confirmation.
- Dashboard and analytics values come from PostgreSQL — nothing is hardcoded.

---

## 2. Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5.3.3, Bootstrap Icons |
| Backend | Python, Flask 3 |
| Database | PostgreSQL, Neon, psycopg 3 |
| Analysis | Pandas, NumPy |
| Charts | Matplotlib (server-rendered SVG) |
| Recommendations | scikit-learn TF-IDF + cosine similarity (optional, with genre fallback) |

Bootstrap and Bootstrap Icons are vendored locally under `app/static/vendor/`, so the layout and icons work without a CDN. All 60 real posters are mirrored under `app/static/img/posters/real/`, so the catalogue renders identically online or offline. Every film also has a generated local SVG cover that appears if the bundled image is unavailable.

---

## 3. Project structure

```text
Project02-mbu/
├── app/
│   ├── __init__.py              # Flask app factory, request user, filters, errors
│   ├── extensions.py            # Request-scoped PostgreSQL connection helpers
│   ├── blueprints/
│   │   ├── dashboard.py         # Dashboard route
│   │   ├── movies.py            # Discover, details, search API
│   │   ├── ratings.py           # Rating submission and My Ratings
│   │   ├── recommendations.py   # Recommendation page
│   │   ├── analytics.py         # Analytics page and chart endpoints
│   │   ├── manage.py            # Movie CRUD
│   │   └── users.py             # Demo profile switching
│   ├── repositories/
│   │   ├── movies.py            # Parameterised movie SQL
│   │   ├── ratings.py           # Rating SQL, aggregates and upsert
│   │   └── users.py             # Demo user SQL
│   ├── services/
│   │   ├── analytics.py         # Pandas/NumPy analysis and weighted ratings
│   │   ├── recommendations.py   # Popular, genre and TF-IDF recommenders
│   │   └── charts.py            # Matplotlib → SVG rendering and cache
│   ├── utils/
│   │   └── validators.py        # Server-side form validation
│   ├── templates/
│   │   ├── base.html            # Shared shell, header, sidebar, flash messages
│   │   ├── macros.html          # Reusable cards, stars, empty states
│   │   ├── partials/sidebar.html
│   │   ├── dashboard.html
│   │   ├── discover.html
│   │   ├── movie_details.html
│   │   ├── recommendations.html
│   │   ├── analytics.html
│   │   ├── manage_movies.html
│   │   ├── my_ratings.html
│   │   └── error.html
│   └── static/
│       ├── css/style.css        # MovieScope design system
│       ├── js/app.js            # Filters, search, modals, poster fallback
│       ├── img/                 # Favicon, fallback poster, covers, cached real posters
│       └── vendor/              # Bootstrap + Bootstrap Icons (MIT)
├── database/
│   ├── schema.sql               # Tables, constraints, indexes
│   ├── seed.sql                 # 60 movies, 15 users, 230 ratings
│   └── init_db.py               # Creates database, schema and seed data
├── config.py                    # Environment-driven configuration
├── run.py                       # Development entry point
├── index.py                     # Vercel Flask entry point
├── vercel.json                  # Vercel project configuration
├── requirements.txt
├── pyproject.toml               # Vercel Python runtime/build settings
├── scripts/prepare_vercel.py    # Copies static assets to Vercel's public directory
├── .env.example
├── .gitignore
└── README.md
```

The separation is deliberate:

- **Blueprints** handle HTTP routes and templates.
- **Repositories** hold all SQL and return dictionary rows.
- **Services** perform Pandas/NumPy analysis, recommendations and chart rendering.
- **Validators** normalise and reject invalid form input before it reaches SQL.

---

## 4. Setup

### Prerequisites

- Python 3.12
- A PostgreSQL database (Neon is supported)
- `pip`

### Step 1 — Create a virtual environment

**Windows (PowerShell / CMD):**

```bat
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

`scikit-learn` powers the optional TF-IDF recommendation path. If it is unavailable, the app automatically falls back to genre affinity — the page still works.

### Step 3 — Configure the environment

Copy the example file:

**Windows:**

```bat
copy .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

Edit `.env` and set your PostgreSQL connection string:

```dotenv
SECRET_KEY=generate-a-random-secret
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=1

DATABASE_URL=postgresql://user:password@host/database?sslmode=require

DEMO_USER_ID=1
MIN_RATING_COUNT=10
```

`.env` is git-ignored. Only `.env.example` is committed.

Generate a secret locally with `python -c "import secrets; print(secrets.token_hex(32))"`.

### Step 4 — Initialise the database

```bash
python database/init_db.py
```

This connects to the database in `DATABASE_URL`, creates the three tables if needed, and loads the demo data without deleting existing rows. Expected output:

```text
Schema ready (users, movies, ratings).
Demo data ready: 60 movies, 15 users and 230 ratings.
```

Use `python database/init_db.py --no-seed` to create empty tables. Re-running the initializer does not delete existing data or duplicate the bundled seed rows.

### Step 5 — Run the app

```bash
python run.py
```

Open <http://127.0.0.1:5000>.

---

## 5. Deploy on Vercel with Neon

The app runs as a Vercel Python Function in Singapore (`sin1`), close to the Neon database, to reduce database round-trip time. Vercel serves the static files from its CDN; the build step copies the bundled assets into `public/static`. The current production deployment is available at <https://moviescope-livid.vercel.app/>.

1. Create a free Neon project and copy its pooled PostgreSQL connection string. Keep the `sslmode=require` parameter in the URL.
2. Set `DATABASE_URL` in your local `.env`, then run `python database/init_db.py` once to create the schema and sample data in Neon.
3. Push this repository to GitHub, then import it in Vercel. The repository root should contain `index.py`, `requirements.txt`, and `pyproject.toml`; leave the build and output settings at their defaults. Automatic deployments require the GitHub account connected to Vercel to have access to this repository. If Vercel cannot import or connect the repository, ask its owner to grant the Vercel GitHub App access to it.
4. In Vercel project settings, add these environment variables for Production and Preview:
   - `DATABASE_URL`: the Neon connection string
   - `SECRET_KEY`: a newly generated value from `python -c "import secrets; print(secrets.token_hex(32))"`
   - `DEMO_USER_ID`: `1` (optional; defaults to `1`)
   - `MIN_RATING_COUNT`: `10` (optional; defaults to `10`)
5. Redeploy and open the deployment URL. If Git integration is not connected, run `vercel link` once in the repository and then run `vercel --prod` after each update.

Do not commit `.env` or paste database credentials into source files. The app expects the Neon schema to be initialised before the first deployment; database setup is a one-time command, not part of each Vercel build. The current deployment uses the Vercel Hobby team and the connected Neon project; verify the providers' current usage quotas before relying on free-tier limits.

Neon and Vercel free-tier quotas and plan terms can change. Usage beyond the current included limits may require payment, so check the providers' pricing pages before deployment.

---

## 6. Demo profiles

MovieScope is an academic prototype, so it deliberately avoids a login system. The header profile menu switches between fifteen seeded users. Every rating is still stored against a real `user_id`, which demonstrates personalisation and privacy.

| User ID | Name | Purpose |
| --- | --- | --- |
| 1 | Aarav Sharma | Default profile, 21 ratings, Science-Fiction/Drama lean |
| 2 | Meera Nair | Animation/Romance lean, 24 ratings |
| 3 | Rohan Verma | Action/Crime lean, 18 ratings |
| 4 | Ananya Iyer | Drama/Romance lean, 19 ratings |
| 5 | Kabir Malhotra | Crime/Thriller lean, harsher scorer, 13 ratings |
| 6 | Sara Khan | Comedy/Animation lean, 18 ratings |
| 7 | Dev Patel | Crime/Thriller lean, 23 ratings |
| 8 | Nisha Rao | Action/Sci-Fi lean, 19 ratings |
| 9 | Arjun Menon | Drama/Thriller lean, 19 ratings |
| 10 | Priya Desai | Sci-Fi/Drama lean, 17 ratings |
| 11 | Ishaan Gupta | Action/Sci-Fi lean, 8 ratings |
| 12 | Tara Krishnan | Romance/Drama lean, 8 ratings |
| 13 | Vikram Sethi | Crime/Thriller lean, 8 ratings |
| 14 | Neha Joshi | Animation/Comedy lean, 8 ratings |
| 15 | Aditya Bose | Drama/Western lean, 7 ratings |

Use the profile switcher to show that **My Ratings** and the header activity panel only ever query the current profile.

---

## 7. Database design

```sql
users (
    user_id INTEGER PK GENERATED BY DEFAULT AS IDENTITY,
    display_name VARCHAR(80) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

movies (
    movie_id INTEGER PK GENERATED BY DEFAULT AS IDENTITY,
    title VARCHAR(150) NOT NULL,
    release_year SMALLINT NOT NULL,
    genre VARCHAR(40) NOT NULL,
    poster_url VARCHAR(500) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

ratings (
    rating_id INTEGER PK GENERATED BY DEFAULT AS IDENTITY,
    user_id INTEGER NOT NULL,
    movie_id INTEGER NOT NULL,
    rating SMALLINT NOT NULL,
    rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_ratings_user_movie (user_id, movie_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id)
        ON DELETE CASCADE ON UPDATE CASCADE
)
```

Additional safeguards:

- `CHECK (rating BETWEEN 1 AND 10)`
- `CHECK (release_year BETWEEN 1888 AND 2100)`
- non-empty title and display-name checks
- indexes on `movies.genre`, `movies.release_year` and `ratings.movie_id`
- `ON DELETE CASCADE` means deleting a movie also removes its ratings

### Query safety

- Every user value is passed through psycopg placeholders (`%s`).
- Sort choices are mapped through a fixed allow-list in `app/repositories/movies.py`; user input never becomes SQL.
- Genre values are validated against the application's configured genre list.
- Poster URLs must be `http://` or `https://` links.

---

## 8. Algorithms explained

### 8.1 Rating aggregation

Average rating and rating count are calculated with SQL `AVG()`/`COUNT()` in the repository layer. The resulting rows are converted to typed Pandas DataFrames for ranking and charting.

### 8.2 Bayesian weighted rating

Popularity lists use the weighted rating formula:

```text
WR = (v / (v + m)) × R + (m / (v + m)) × C
```

| Symbol | Meaning |
| --- | --- |
| `R` | Movie average rating |
| `v` | Number of ratings for the movie |
| `m` | Minimum rating count threshold (`MIN_RATING_COUNT`, default `10`) |
| `C` | Overall average rating across all ratings |

A movie with many ratings is trusted more; a movie with very few ratings is pulled toward the catalogue average. `m` is configurable in `.env`.

Example: a movie with `R = 9.5`, `v = 4`, `C = 8.1`, `m = 10`:

```text
WR = (4 / 14) × 9.5 + (10 / 14) × 8.1 = 2.71 + 5.79 = 8.50
```

The same formula powers the dashboard's featured movies and the “Popular now” recommendation section.

### 8.3 Top-rated ranking

Top-rated lists require at least three ratings (`TOP_RATED_MIN_COUNT`) to avoid a single enthusiastic score dominating the leaderboard. Remaining ties are broken by rating count.

### 8.4 Genre-based recommendations

The user's highest-rated genre is calculated from their own rating history:

```sql
SELECT genre, AVG(rating), COUNT(*)
FROM ratings JOIN movies ...
WHERE user_id = %s
GROUP BY genre
ORDER BY AVG(rating) DESC, COUNT(*) DESC
LIMIT 1
```

Movies from that genre are then ranked by weighted score, and movies the user has already rated are removed. A visitor can override the automatic choice with the genre pills on the page.

### 8.5 Content similarity (TF-IDF + cosine)

For “Picked for you” and “More like this”:

1. Build a text document for every movie: `"<title> <genre> <genre>"`. Repeating the genre gives it more weight.
2. Vectorise the documents with `TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)`.
3. Compute cosine similarity between all movie vectors.
4. Seed the profile with the current user's ratings of 8/10 or higher.
5. Average the seed vectors, compare that profile against every unrated movie, and return the strongest matches.
6. Explain each result using the most similar seed: *“Because you rated Parasite 9/10 and both are Thriller films with a similar tone.”*

If scikit-learn is missing or the corpus is too small, the service falls back to the user's preferred genre, so the page never fails.

### 8.6 Analytics and chart caching

Matplotlib runs with the `Agg` backend and renders four SVGs: rating distribution, average rating by genre, top-rated movies and rating volume. Genres are calculated from individual ratings (not by averaging movie averages).

Generated charts are cached in memory until the underlying data changes. The cache signature includes rating count, rating sum, latest rating timestamp, movie count and a PostgreSQL hash signature of movie titles/years/genres.

---

## 9. Design system

The interface follows the supplied MovieScope direction: a light cinema/SaaS workspace with a fixed sidebar, sticky white header, reusable cards, restrained shadows and a consistent 8px spacing rhythm.

### Core tokens

| Token | Value |
| --- | --- |
| Green (primary) | `#087F69` |
| Ocean blue | `#3978CE` |
| Royal violet | `#8856C8` |
| Coral | `#E87969` |
| Amber gold | `#D78B16` |
| Deep teal | `#123B46` |
| Background | `#F3F7F8` |
| Card | `#FFFFFF` |
| Border | `#E5ECEE` |
| Card radius | `14px` |
| Control radius | `10px` |

The brand mark is a minimal clapperboard. “Movie” is deep teal, “Scope” is green, and the tagline is *Every movie has a story.*

### Responsive behaviour

- Desktop: fixed 260px sidebar with the workspace navigation.
- Tablet: the 4-column featured grid folds to 2 columns.
- Mobile: sidebar becomes a Bootstrap offcanvas panel; movie grids become two columns; filters and forms stack; tables scroll horizontally.
- Motion is reduced automatically when the user prefers reduced motion.

### Reusable UI pieces

Movie cards, star ratings, stat cards, section headers, empty states, filter chips, rank chips, tables, modals and alerts are defined once in `macros.html` and `style.css`, then reused across all pages.

---

## 10. Routes

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/` | Dashboard |
| GET | `/discover` | Search, filter and sort catalogue |
| GET | `/movies/<id>` | Movie details and distribution |
| POST | `/movies/<id>/rate` | Create or update a rating |
| GET | `/my-ratings` | Current profile's ratings |
| POST | `/my-ratings/update` | Update an existing rating |
| GET | `/recommendations` | Personal, popular, top-rated and genre picks |
| GET | `/analytics` | Analytics page |
| GET | `/analytics/chart/<name>.svg` | Generated chart image |
| GET | `/manage` | Movie management table |
| POST | `/manage/add` | Add a movie |
| POST | `/manage/<id>/edit` | Edit a movie |
| POST | `/manage/<id>/delete` | Delete a movie and its ratings |
| GET | `/api/search?q=` | JSON title suggestions |
| POST | `/switch-user/<id>` | Switch demo profile |

---

## 11. Suggested viva walkthrough

1. **Dashboard:** point out that totals come from PostgreSQL; open a featured movie.
2. **Discover:** combine `genre = Sci-Fi`, `year = 2014`, `sort = highest rating`; note that the URL carries all filters.
3. **Movie Details:** rate the film 9/10, then submit again with a different score to show the update-in-place behaviour and the distribution changing.
4. **Recommendations:** switch from “Auto · my taste” to another genre; hover the explanation notes.
5. **Analytics:** show the four charts, the weighted-score column and the formula panel. Explain why `m = 10` prevents small samples from dominating.
6. **Manage Movies:** add a title, edit it, then open the delete dialog and cancel; delete it to show the cascade.
7. **My Ratings:** update a score, then switch demo profile and show that the history changes and no other user's private ratings appear.

---

## 12. Troubleshooting

| Problem | Fix |
| --- | --- |
| PostgreSQL authentication/connection error | Check `DATABASE_URL`, including its password and `sslmode=require` parameter. |
| Empty or missing tables | Set `DATABASE_URL`, then run `python database/init_db.py`. |
| Port 5000 already in use | Change `FLASK_PORT` in `.env` or stop the other process. |
| Charts take a second on first load | Matplotlib imports and builds its font cache once; subsequent requests use the cache. |
| Poster images are blank | Locally, posters are served from `app/static/`; Vercel serves the generated `public/static/` assets from its CDN. |
| Recommendations lack personal picks | The current profile must have at least one rating. Rate a movie first. |
| Changes to `.env` are ignored | Restart `python run.py`; configuration is loaded at startup. |

---

## 13. Academic scope and limitations

This is a teaching prototype, not a production platform:

- There is **no authentication**; demo profiles are switched intentionally from the header. A production version would use hashed passwords, server-side sessions and CSRF protection.
- Rating history is private in the sense that queries are always scoped to the active profile; there is no admin view of other users' histories.
- The catalogue is intentionally moderate (60 films) and stored in one table with a single genre per movie.
- Recommendations are explainable heuristics, not a production machine-learning system.
- The seed data is curated for demonstration; it is not a live film database.

---

## 14. Credits

- [Flask](https://flask.palletsprojects.com/), [psycopg](https://www.psycopg.org/), [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/), [Matplotlib](https://matplotlib.org/), [scikit-learn](https://scikit-learn.org/)
- [Bootstrap 5.3.3](https://getbootstrap.com/) and [Bootstrap Icons 1.11.3](https://icons.getbootstrap.com/) — MIT licenses included in `app/static/vendor/`
- Poster artwork comes from [TMDB](https://www.themoviedb.org/) and is mirrored locally for reliable, offline-friendly demos; generated SVG covers are original MovieScope assets.
- Typeface: Plus Jakarta Sans, loaded from Google Fonts with a system-font fallback.
