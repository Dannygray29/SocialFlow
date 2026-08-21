"""SocialFlow cloud worker entrypoint.

Runs one autonomous unit at a time so it can execute safely on an ephemeral
runner such as GitHub Actions. State is persisted by the workflow artifact.
"""
import asyncio
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from main import (
    CONFIG,
    init_db,
    init_brand_tables,
    init_signals_table,
    init_plans_table,
    get_automation,
    _run_pipeline_job,
    _run_scout_job,
    _run_analyst_job,
)
from agents.orchestrator import run_publish_only


def initialize() -> None:
    init_db()
    init_brand_tables()
    init_signals_table()
    init_plans_table()


async def run(mode: str) -> None:
    initialize()
    print(f"[SocialFlow worker] mode={mode}")
    print(f"[SocialFlow worker] AI_PROVIDER={CONFIG.get('AI_PROVIDER')}")

    if mode == "pipeline":
        await _run_pipeline_job(skip_publish=True)
    elif mode == "scout":
        await _run_scout_job()
    elif mode == "publish":
        await run_publish_only(automation_getter=get_automation)
    elif mode == "analyst":
        await _run_analyst_job()
    else:
        raise SystemExit(f"Unknown mode: {mode}")


if __name__ == "__main__":
    asyncio.run(run(os.getenv("SOCIALFLOW_MODE", "pipeline")))
