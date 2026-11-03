"""Create the MovieScope PostgreSQL schema and optionally load demo data.

Usage:
    python database/init_db.py
    python database/init_db.py --no-seed

Reads DATABASE_URL from the environment or the project's .env file.
"""

import argparse
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def split_sql(script):
    """Split the bundled SQL files into statements."""
    statements = []
    buffer = []
    for line in script.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        buffer.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(buffer).rstrip(";"))
            buffer = []
    if buffer:
        statements.append("\n".join(buffer))
    return [statement for statement in statements if statement.strip()]


def main():
    parser = argparse.ArgumentParser(
        description="Initialise the MovieScope PostgreSQL database."
    )
    parser.add_argument(
        "--no-seed", action="store_true", help="Create tables but skip demo data."
    )
    args = parser.parse_args()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required. Set it in .env or your environment.")

    print("Connecting to PostgreSQL...")
    try:
        with psycopg.connect(
            database_url, connect_timeout=5, prepare_threshold=None
        ) as connection:
            with connection.cursor() as cursor:
                schema_path = Path(__file__).with_name("schema.sql")
                for statement in split_sql(schema_path.read_text(encoding="utf-8")):
                    cursor.execute(statement)
                print("Schema ready (users, movies, ratings).")

                if not args.no_seed:
                    seed_path = Path(__file__).with_name("seed.sql")
                    for statement in split_sql(seed_path.read_text(encoding="utf-8")):
                        cursor.execute(statement)

                    for table, column in (
                        ("users", "user_id"),
                        ("movies", "movie_id"),
                        ("ratings", "rating_id"),
                    ):
                        cursor.execute(
                            f"""
                            SELECT setval(
                                pg_get_serial_sequence(%s, %s),
                                COALESCE(MAX({column}), 1),
                                COUNT(*) > 0
                            )
                            FROM {table}
                            """,
                            (table, column),
                        )

                    cursor.execute("SELECT COUNT(*) FROM movies")
                    movie_count = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM ratings")
                    rating_count = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM users")
                    user_count = cursor.fetchone()[0]
                    print(
                        f"Demo data ready: {movie_count} movies, {user_count} users "
                        f"and {rating_count} ratings."
                    )

        print("Done. Start the app with: python run.py")
    except psycopg.Error as error:
        raise SystemExit(
            f"Could not initialise PostgreSQL: {error}\n"
            "Check DATABASE_URL and confirm the Neon database is reachable."
        ) from error


if __name__ == "__main__":
    sys.exit(main())
