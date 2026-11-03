"""Copy Flask's local static assets into Vercel's CDN-served public directory."""

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "app" / "static"
DESTINATION = ROOT / "public" / "static"

if not SOURCE.is_dir():
    raise SystemExit(f"Static asset directory not found: {SOURCE}")

shutil.copytree(SOURCE, DESTINATION, dirs_exist_ok=True)
print(f"Copied static assets from {SOURCE} to {DESTINATION}.")
