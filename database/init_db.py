"""Create the MovieScope database, schema and demo data.

Usage:
    python database/init_db.py
    python database/init_db.py --no-seed

Reads MySQL connection details from the project's .env file (or environment).
"""

import argparse
import os
import re
import sys
from pathlib import Path

import pymysql
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def split_sql(script):
    """Split simple DDL/DML scripts into statements.

    The bundled scripts do not contain stored procedures or semicolons inside
    string literals, so a straightforward split is safe and keeps setup easy to
    follow for a student project.
    """
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
    parser = argparse.ArgumentParser(description="Initialise the MovieScope MySQL database.")
    parser.add_argument("--no-seed", action="store_true", help="Create tables but skip demo data.")
    args = parser.parse_args()

    host = os.getenv("DB_HOST", "127.0.0.1")
    port = int(os.getenv("DB_PORT", "3306"))
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "moviescope")

    if not re.fullmatch(r"[A-Za-z0-9_]+", database):
        raise SystemExit("DB_NAME may only contain letters, numbers and underscores.")

    print(f"Connecting to MySQL at {host}:{port} as {user}...")
    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset="utf8mb4",
            autocommit=True,
        )
    except pymysql.MySQLError as error:
        raise SystemExit(
            f"Could not connect to MySQL: {error}\n"
            "Check that MySQL is running and your .env credentials are correct."
        )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cursor.execute(f"USE `{database}`")
            print(f"Database ready: {database}")

            schema_path = Path(__file__).with_name("schema.sql")
            for statement in split_sql(schema_path.read_text(encoding="utf-8")):
                cursor.execute(statement)
            print("Schema created (users, movies, ratings).")

            if not args.no_seed:
                seed_path = Path(__file__).with_name("seed.sql")
                for statement in split_sql(seed_path.read_text(encoding="utf-8")):
                    cursor.execute(statement)
                cursor.execute("SELECT COUNT(*) FROM movies")
                movie_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM ratings")
                rating_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                print(
                    f"Seeded {movie_count} movies, {user_count} users and "
                    f"{rating_count} ratings."
                )

        print("Done. Start the app with: python run.py")
    finally:
        connection.close()


if __name__ == "__main__":
    sys.exit(main())
