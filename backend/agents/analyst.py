"""
Analyst Agent — Performance + Learning

Responsibilities:
  - Track posts per platform, success/failure rates
  - Generate daily summary reports
  - Provide dashboard analytics data
  - Feed insights back to Planner

Runs: End of day (or on-demand via API)
"""

import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List

DB_PATH = Path(__file__).parent.parent / "socialflow.db"


def get_daily_stats(target_date: str = None) -> Dict:
    """Get posting stats for a specific date."""
    if not target_date:
        target_date = date.today().isoformat()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Posts by platform and status
    rows = conn.execute("""
        SELECT platform, status, COUNT(*) as count
        FROM posts
        WHERE DATE(created_at) = ?
        GROUP BY platform, status
    """, (target_date,)).fetchall()

    stats = {}
    for row in rows:
        p = row["platform"]
        if p not in stats:
            stats[p] = {"draft": 0, "approved": 0, "posted": 0, "failed": 0, "review": 0, "blocked": 0}
        stats[p][row["status"]] = row["count"]

    # Signals fetched
    signal_count = conn.execute(
        "SELECT COUNT(*) FROM signals WHERE DATE(fetched_at) = ?", (target_date,)
    ).fetchone()[0]

    # Plans created
    plan_count = conn.execute(
        "SELECT COUNT(*) FROM content_plans WHERE DATE(created_at) = ?", (target_date,)
    ).fetchone()[0]

    conn.close()

    total_posted = sum(s.get("posted", 0) for s in stats.values())
    total_failed = sum(s.get("failed", 0) for s in stats.values())

    return {
        "date": target_date,
        "signals_fetched": signal_count,
        "plans_created": plan_count,
        "platforms": stats,
        "total_posted": total_posted,
        "total_failed": total_failed,
        "success_rate": round(total_posted / max(total_posted + total_failed, 1) * 100, 1),
    }


def get_weekly_stats() -> Dict:
    """Get stats for the past 7 days."""
    days = []
    for i in range(7):
        d = (date.today() - timedelta(days=i)).isoformat()
        days.append(get_daily_stats(d))

    total_posted = sum(d["total_posted"] for d in days)
    total_failed = sum(d["total_failed"] for d in days)

    return {
        "period": "7 days",
        "days": days,
        "total_posted": total_posted,
        "total_failed": total_failed,
        "avg_posts_per_day": round(total_posted / 7, 1),
        "success_rate": round(total_posted / max(total_posted + total_failed, 1) * 100, 1),
    }


def get_top_performing_posts(limit: int = 5) -> List[Dict]:
    """Get recent posted content (for dashboard)."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT * FROM posts
        WHERE status = 'posted'
        ORDER BY published_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


async def run():
    """Generate daily analytics report."""
    print(f"[Analyst] Starting at {datetime.now().strftime('%H:%M:%S')}")

    stats = get_daily_stats()
    print(f"[Analyst] Today: {stats['total_posted']} posted, {stats['total_failed']} failed")
    print(f"[Analyst] Signals: {stats['signals_fetched']}, Plans: {stats['plans_created']}")
    for platform, counts in stats.get("platforms", {}).items():
        print(f"[Analyst]   {platform}: {counts}")

    weekly = get_weekly_stats()
    print(f"[Analyst] Week: {weekly['total_posted']} posts, {weekly['avg_posts_per_day']}/day avg")

    return stats
