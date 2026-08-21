"""
Planner Agent — Content Strategy

Responsibilities:
  - Read unprocessed signals from Scout
  - Decide: what to post, which platform, what format, what time
  - Apply rate-limits and platform best practices
  - Avoid duplicates and topic repetition
  - Create content plans in SQLite

Runs: After Scout completes
"""

import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict

DB_PATH = Path(__file__).parent.parent / "socialflow.db"

PLATFORM_FORMATS = {
    "linkedin": {"max_chars": 3000, "supports_image": True, "supports_carousel": True},
    "x": {"max_chars": 280, "supports_image": True, "supports_carousel": False},
    "discord": {"max_chars": 2000, "supports_image": True, "supports_carousel": False},
    "instagram": {"max_chars": 2200, "supports_image": True, "supports_carousel": True},
    "reddit": {"max_chars": 40000, "supports_image": False, "supports_carousel": False},
    "facebook": {"max_chars": 63206, "supports_image": True, "supports_carousel": True},
    "youtube": {"max_chars": 5000, "supports_image": False, "supports_carousel": False, "supports_video": True},
}

DEFAULT_LIMITS = {
    "linkedin": {"daily_cap": 2, "windows": [11, 23]},
    "x": {"daily_cap": 5, "windows": None},
    "discord": {"daily_cap": 10, "windows": None},
    "instagram": {"daily_cap": 3, "windows": None},
    "reddit": {"daily_cap": 1, "windows": None},
    "facebook": {"daily_cap": 3, "windows": [11, 18]},
    "youtube": {"daily_cap": 1, "windows": [19]},
}


def init_plans_table():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute('''CREATE TABLE IF NOT EXISTS content_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        signal_id INTEGER,
        platform TEXT NOT NULL,
        content_type TEXT NOT NULL,
        priority INTEGER DEFAULT 5,
        scheduled_hour INTEGER,
        status TEXT DEFAULT 'planned',
        brief TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (signal_id) REFERENCES signals(id)
    )''')
    conn.commit()
    conn.close()


def get_todays_plan_count(platform: str) -> int:
    conn = sqlite3.connect(str(DB_PATH))
    today = date.today().isoformat()
    count = conn.execute("SELECT COUNT(*) FROM content_plans WHERE platform = ? AND DATE(created_at) = ?", (platform, today)).fetchone()[0]
    conn.close()
    return count


def get_todays_post_count(platform: str) -> int:
    conn = sqlite3.connect(str(DB_PATH))
    today = date.today().isoformat()
    count = conn.execute("SELECT COUNT(*) FROM posts WHERE platform = ? AND status = 'posted' AND DATE(published_at) = ?", (platform, today)).fetchone()[0]
    conn.close()
    return count


def create_plan(signal_id: int, platform: str, content_type: str, priority: int = 5, scheduled_hour: int = None, brief: str = ""):
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "INSERT INTO content_plans (signal_id, platform, content_type, priority, scheduled_hour, brief) VALUES (?, ?, ?, ?, ?, ?)",
        (signal_id, platform, content_type, priority, scheduled_hour, brief)
    )
    conn.commit()
    conn.close()


def _can_plan(platform: str) -> bool:
    limits = DEFAULT_LIMITS.get(platform, {})
    cap = limits.get("daily_cap", 5)
    return get_todays_plan_count(platform) + get_todays_post_count(platform) < cap


def plan_signal(signal: Dict) -> List[Dict]:
    plans = []
    title = signal.get("title", "")
    signal_type = signal.get("signal_type", "news")
    score = signal.get("score", 0)
    relevance = signal.get("relevance_score", 0)

    if signal_type == "news" and (relevance > 0.3 or score > 100):
        targets = [("facebook", 11), ("youtube", 19), ("linkedin", 11), ("x", None), ("discord", None)]
        for platform, hour in targets:
            if _can_plan(platform):
                content_type = "ai-news-video" if platform == "youtube" else "ai-news"
                create_plan(
                    signal_id=signal["id"], platform=platform, content_type=content_type,
                    priority=min(10, score // 50 + int(relevance * 5)), scheduled_hour=hour,
                    brief=f"Create platform-native content about: {title}"
                )
                plans.append({"platform": platform, "type": content_type})

    elif signal_type == "news" and relevance > 0.1:
        if _can_plan("facebook"):
            create_plan(signal["id"], "facebook", "ai-news", priority=3, scheduled_hour=18, brief=f"Quick news update: {title}")
            plans.append({"platform": "facebook", "type": "ai-news"})

    elif signal_type in ("repo", "release"):
        for platform in ["facebook", "linkedin", "youtube", "reddit"]:
            if _can_plan(platform):
                content_type = "repo-video" if platform == "youtube" else "repo-promo"
                create_plan(signal["id"], platform, content_type, priority=7, scheduled_hour=19 if platform == "youtube" else None, brief=f"Promote repo: {title}")
                plans.append({"platform": platform, "type": content_type})

    return plans


async def run():
    from agents.scout import get_unprocessed_signals, mark_processed
    init_plans_table()
    print(f"[Planner] Starting at {datetime.now().strftime('%H:%M:%S')}")
    signals = get_unprocessed_signals(limit=15)
    print(f"[Planner] Processing {len(signals)} unprocessed signals")
    total_plans = 0
    processed_ids = []
    for signal in signals:
        plans = plan_signal(signal)
        total_plans += len(plans)
        processed_ids.append(signal["id"])
        if plans:
            print(f"[Planner] Signal '{signal['title'][:50]}' → {', '.join(p['platform'] for p in plans)}")
    if processed_ids:
        mark_processed(processed_ids)
    print(f"[Planner] Done — {total_plans} plans created from {len(signals)} signals")
    return total_plans


def get_pending_plans(limit: int = 20) -> List[Dict]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute('''
        SELECT cp.*, s.title as signal_title, s.url as signal_url, s.summary as signal_summary,
               s.source as signal_source
        FROM content_plans cp
        JOIN signals s ON cp.signal_id = s.id
        WHERE cp.status = 'planned'
        ORDER BY cp.priority DESC, cp.created_at ASC
        LIMIT ?
    ''', (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_plan_completed(plan_id: int):
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("UPDATE content_plans SET status = 'completed' WHERE id = ?", (plan_id,))
    conn.commit()
    conn.close()
