"""
Agent Orchestrator — Coordinates the 6-agent pipeline

Pipeline: Scout → Planner → Creator → Reviewer → Publisher → Analyst

Each agent runs sequentially. The orchestrator is triggered by:
  - APScheduler (automatic daily schedule)
  - Manual API call (POST /api/pipeline/run)
  - Dashboard "Run Pipeline" button
"""

import asyncio
from datetime import datetime
from typing import Callable, Optional

from agents import scout, planner, creator, reviewer, publisher, analyst


class PipelineStatus:
    """Track current pipeline state for the dashboard."""
    def __init__(self):
        self.running = False
        self.current_agent = None
        self.last_run = None
        self.last_result = {}
        self.error = None

    def to_dict(self):
        return {
            "running": self.running,
            "current_agent": self.current_agent,
            "last_run": self.last_run,
            "last_result": self.last_result,
            "error": self.error,
        }


# Global status
status = PipelineStatus()


async def run_full_pipeline(ai_generate_fn: Callable = None,
                            automation_getter: Callable = None,
                            skip_publish: bool = False):
    """Run the complete pipeline: Scout → Planner → Creator → Reviewer → [Publisher] → Analyst.

    Args:
        ai_generate_fn: Async function for content generation (from main.py)
        automation_getter: Function(platform) -> automation instance (from automation.py)
        skip_publish: If True, skip Publisher agent (useful for manual review first)
    """
    if status.running:
        print("[Orchestrator] Pipeline already running — skipping")
        return status.last_result

    status.running = True
    status.error = None
    result = {}

    try:
        # Agent 1: Scout
        status.current_agent = "scout"
        print("\n[Orchestrator] ═══ STAGE 1: SCOUT ═══")
        result["scout"] = await scout.run()

        # Agent 2: Planner
        status.current_agent = "planner"
        print("\n[Orchestrator] ═══ STAGE 2: PLANNER ═══")
        result["planner"] = await planner.run()

        # Agent 3: Creator
        status.current_agent = "creator"
        print("\n[Orchestrator] ═══ STAGE 3: CREATOR ═══")
        result["creator"] = await creator.run(ai_generate_fn=ai_generate_fn)

        # Agent 4: Reviewer
        status.current_agent = "reviewer"
        print("\n[Orchestrator] ═══ STAGE 4: REVIEWER ═══")
        result["reviewer"] = await reviewer.run()

        # Agent 5: Publisher (optional — skip if manual review preferred)
        if not skip_publish:
            status.current_agent = "publisher"
            print("\n[Orchestrator] ═══ STAGE 5: PUBLISHER ═══")
            result["publisher"] = await publisher.run(automation_getter=automation_getter)
        else:
            result["publisher"] = "skipped"
            print("\n[Orchestrator] ═══ STAGE 5: PUBLISHER (skipped — manual review mode) ═══")

        # Agent 6: Analyst
        status.current_agent = "analyst"
        print("\n[Orchestrator] ═══ STAGE 6: ANALYST ═══")
        result["analyst"] = await analyst.run()

        status.last_result = result
        status.last_run = datetime.now().isoformat()
        print(f"\n[Orchestrator] ═══ PIPELINE COMPLETE ═══")

    except Exception as e:
        status.error = str(e)
        print(f"\n[Orchestrator] PIPELINE ERROR at {status.current_agent}: {e}")
        result["error"] = str(e)

    finally:
        status.running = False
        status.current_agent = None

    return result


async def run_scout_only():
    """Run just the Scout agent (news fetch)."""
    return await scout.run()


async def run_publish_only(automation_getter=None):
    """Run just the Publisher agent (for posting window triggers)."""
    return await publisher.run(automation_getter=automation_getter)


async def run_analyst_only():
    """Run just the Analyst agent (daily report)."""
    return await analyst.run()
