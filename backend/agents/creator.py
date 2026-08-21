"""
Creator Agent — Content Production
"""

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

DB_PATH = Path(__file__).parent.parent / "socialflow.db"

PLATFORM_PROMPTS = {
    "linkedin": {
        "ai-news": "Write a LinkedIn post (max 500 chars) about this AI news. First person, founder voice. 3 short paragraphs. End with 2-3 relevant hashtags. No hype.",
        "repo-promo": "Write a LinkedIn post (max 400 chars) announcing this open-source repo. First person, founder perspective. Why it matters, who it's for. End with GitHub link + 2 hashtags.",
    },
    "x": {
        "ai-news": "Write a tweet (max 270 chars) about this AI news. Direct, factual. One key takeaway. Include the source URL.",
        "repo-promo": "Write a tweet (max 270 chars) announcing this open-source repo. What it does + GitHub link.",
    },
    "discord": {
        "ai-news": "Write a short Discord message (max 300 chars) about this AI news. Direct, factual, 1-2 sentences. Max 1 emoji. End with the source link.",
        "repo-promo": "Write a Discord announcement (max 300 chars) for this new repo. What it does + link.",
    },
    "reddit": {
        "ai-news": "Write a Reddit post title (max 200 chars, factual, no clickbait) and body (3 paragraphs, max 500 chars). Include source URL at the end.",
        "repo-promo": "Write a Reddit post title and body announcing this open-source repo. Factual, useful, not promotional. Include GitHub link.",
    },
    "instagram": {
        "ai-news": "Write an Instagram caption (max 300 chars) about this AI news. Engaging, educational. 5-8 relevant hashtags. No links (use 'link in bio').",
        "repo-promo": "Write an Instagram caption (max 300 chars) for this repo launch. Include 5-8 hashtags.",
    },
    "facebook": {
        "ai-news": "Write a Facebook Page post (max 900 chars) about this AI news. Start with a strong but factual hook, explain why it matters, and end with one question to encourage comments. Include the source URL.",
        "repo-promo": "Write a Facebook Page post (max 900 chars) announcing this open-source repo. Explain the problem it solves, who benefits, and include the GitHub link.",
    },
    "youtube": {
        "ai-news-video": "Create a YouTube Short package about this AI news. Return: TITLE (max 70 chars), HOOK (first 2 seconds), SCRIPT (45-60 seconds, spoken naturally), DESCRIPTION (max 1000 chars), 5 HASHTAGS, VIDEO_PROMPT (visual scene instructions for an AI video generator). Be factual and avoid unsupported claims.",
        "repo-video": "Create a YouTube Short package promoting this open-source repo. Return: TITLE, HOOK, 45-60 second SCRIPT, DESCRIPTION with link, 5 HASHTAGS, VIDEO_PROMPT. Be useful rather than hype-driven.",
    },
}

BANNED_PHRASES = [
    "In conclusion", "it's worth noting", "This is exciting", "Exciting news",
    "thrilled to share", "game-changer", "revolutionizing", "As an AI",
    "I cannot", "I'm unable", "dive in", "dive deep", "let's dive",
    "In today's", "ensure", "notably", "utilize", "Furthermore",
    "Moreover", "Additionally", "cutting-edge", "groundbreaking",
    "innovative", "seamless", "robust", "comprehensive", "delve",
    "fostering", "leveraging", "embrace",
]


def get_brand_config() -> Dict:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM brand_config ORDER BY id DESC LIMIT 1").fetchone()
        if row:
            data = dict(row)
            conn.close()
            return data
    except sqlite3.OperationalError:
        pass
    conn.close()
    return {
        "brand_name": "GreySocial",
        "primary_color": "#0A74DA",
        "secondary_color": "#F5A623",
        "dark_bg": "#1A1A2E",
        "tone": "clear, direct, practical, builder-minded",
        "forbidden_styles": "robot heads, stock photos, neon, clipart",
    }


def build_prompt(plan: Dict) -> str:
    platform = plan["platform"]
    content_type = plan["content_type"]
    title = plan.get("signal_title", "")
    url = plan.get("signal_url", "")
    summary = plan.get("signal_summary", "")
    brand = get_brand_config()
    template = PLATFORM_PROMPTS.get(platform, {}).get(content_type, f"Write a {platform} post about this topic. Keep it short and useful.")
    return f"""{template}\n\nTopic: {title}\nSource URL: {url}\nSummary: {summary}\nBrand voice: {brand.get('tone', 'direct and practical')}\nForbidden phrases: {', '.join(BANNED_PHRASES[:15])}\n"""


def clean_generated_text(text: str) -> str:
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    text = re.sub(r'^```\w*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'```$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^(Here\'s|Here is|Sure,?|Of course,?).*?:\s*\n', '', text, flags=re.IGNORECASE)
    return text.strip()


async def generate_post_content(plan: Dict, ai_generate_fn) -> Optional[str]:
    try:
        return clean_generated_text(await ai_generate_fn(build_prompt(plan)))
    except Exception as e:
        print(f"[Creator] AI generation failed for plan {plan['id']}: {e}")
        return None


def save_draft(platform: str, content: str, content_type: str, signal_url: str = "", plan_id: int = None):
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("INSERT INTO posts (platform, content_type, content, status, created_at) VALUES (?, ?, ?, 'draft', ?)", (platform, content_type, content, datetime.now().isoformat()))
    post_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    return post_id


async def run(ai_generate_fn=None):
    from agents.planner import get_pending_plans, mark_plan_completed
    print(f"[Creator] Starting at {datetime.now().strftime('%H:%M:%S')}")
    plans = get_pending_plans(limit=10)
    print(f"[Creator] {len(plans)} pending plans to process")
    created = 0
    for plan in plans:
        content = await generate_post_content(plan, ai_generate_fn) if ai_generate_fn else f"{plan.get('signal_title', '')}\n\n{plan.get('signal_summary', '')}\n\n{plan.get('signal_url', '')}"
        if content and len(content.strip()) > 20:
            post_id = save_draft(plan["platform"], content, plan["content_type"], plan.get("signal_url", ""), plan["id"])
            mark_plan_completed(plan["id"])
            created += 1
            print(f"[Creator] Draft #{post_id} for {plan['platform']}: {content[:60]}...")
    print(f"[Creator] Done — {created} drafts created")
    return created
