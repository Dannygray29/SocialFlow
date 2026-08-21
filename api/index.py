import os
import sys

# Make the existing SocialFlow backend importable from Vercel's Python runtime.
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)
os.environ.setdefault("VERCEL", "1")

from main import app

__all__ = ["app"]
