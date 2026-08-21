import os
import sys
from contextlib import asynccontextmanager

# Make the existing SocialFlow backend importable from Vercel's Python runtime.
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)
os.environ.setdefault("VERCEL", "1")

from main import app, init_db, init_brand_tables, init_signals_table, init_plans_table
from x_oauth import router as x_oauth_router

app.include_router(x_oauth_router)


@asynccontextmanager
async def vercel_lifespan(_app):
    # Vercel functions are ephemeral; do not start SocialFlow's APScheduler here.
    # The persistent worker runs separately.
    init_db()
    init_brand_tables()
    init_signals_table()
    init_plans_table()
    yield


app.router.lifespan_context = vercel_lifespan

__all__ = ["app"]
