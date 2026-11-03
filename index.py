"""Vercel entrypoint for the MovieScope Flask application."""

from app import create_app

app = create_app()
