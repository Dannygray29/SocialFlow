"""
Brand Kit — API endpoints for brand configuration

Stores and serves brand identity settings:
  - Colors (primary, secondary, dark background)
  - Logo (file upload)
  - Typography (font family, heading weight)
  - Tone and voice guidelines
  - Forbidden styles for image generation
  - Platform-specific hashtags
  - CTA templates
  - Product list with URLs
"""

import json
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

router = APIRouter(prefix="/api/brand", tags=["Brand Kit"])

DB_PATH = Path(__file__).parent / "socialflow.db"
UPLOADS_DIR = Path(__file__).parent / "uploads"


def init_brand_tables():
    """Create brand_config table."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute('''CREATE TABLE IF NOT EXISTS brand_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_name TEXT DEFAULT 'InBharat AI',
        tagline TEXT DEFAULT 'Building practical, accessible AI tools for India',
        primary_color TEXT DEFAULT '#0A74DA',
        secondary_color TEXT DEFAULT '#F5A623',
        dark_bg TEXT DEFAULT '#1A1A2E',
        light_bg TEXT DEFAULT '#FFFFFF',
        success_color TEXT DEFAULT '#10B981',
        warning_color TEXT DEFAULT '#F59E0B',
        danger_color TEXT DEFAULT '#E94560',
        logo_path TEXT DEFAULT '',
        primary_font TEXT DEFAULT 'Roboto',
        heading_weight TEXT DEFAULT '700',
        body_weight TEXT DEFAULT '400',
        code_font TEXT DEFAULT 'JetBrains Mono',
        tone TEXT DEFAULT 'clear, direct, knowledgeable, practical, builder-minded',
        forbidden_styles TEXT DEFAULT 'robot heads, stock photos, neon, clipart, sci-fi dystopia, childish cartoons',
        hashtags_linkedin TEXT DEFAULT '#AI #InBharat #MachineLearning',
        hashtags_x TEXT DEFAULT '#AI #InBharat',
        hashtags_instagram TEXT DEFAULT '#AI #ArtificialIntelligence #InBharat #IndiaAI #MachineLearning #Tech #Startups',
        cta_template TEXT DEFAULT 'Follow @inbharat.ai for daily AI updates',
        products_json TEXT DEFAULT '[]',
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # Insert default if empty
    count = conn.execute("SELECT COUNT(*) FROM brand_config").fetchone()[0]
    if count == 0:
        products = json.dumps([
            {"name": "InBharat AI", "url": "https://inbharat.ai", "description": "AI Consulting & Solutions"},
            {"name": "Phoring", "url": "https://phoring.in", "description": "Decision intelligence platform"},
            {"name": "UniAssist", "url": "https://uniassist.ai", "description": "University guidance AI"},
            {"name": "Testsprep", "url": "https://testsprep.in", "description": "AI test preparation"},
            {"name": "Sahaayak AI", "url": "https://inbharat.ai", "description": "Personal AI assistant for India"},
            {"name": "CodeIn", "url": "https://codein.pro", "description": "Developer tools"},
        ])
        conn.execute("INSERT INTO brand_config (products_json) VALUES (?)", (products,))
        conn.commit()
    conn.close()


class BrandUpdate(BaseModel):
    brand_name: Optional[str] = None
    tagline: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    dark_bg: Optional[str] = None
    light_bg: Optional[str] = None
    primary_font: Optional[str] = None
    tone: Optional[str] = None
    forbidden_styles: Optional[str] = None
    hashtags_linkedin: Optional[str] = None
    hashtags_x: Optional[str] = None
    hashtags_instagram: Optional[str] = None
    cta_template: Optional[str] = None
    products_json: Optional[str] = None


class ProductItem(BaseModel):
    name: str
    url: str
    description: str = ""


@router.get("/config")
async def get_brand_config():
    """Get current brand configuration."""
    init_brand_tables()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM brand_config ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="No brand config found")
    config = dict(row)
    # Parse products JSON
    try:
        config["products"] = json.loads(config.get("products_json", "[]"))
    except json.JSONDecodeError:
        config["products"] = []
    return config


@router.put("/config")
async def update_brand_config(update: BrandUpdate):
    """Update brand configuration."""
    init_brand_tables()
    conn = sqlite3.connect(str(DB_PATH))

    # Build dynamic UPDATE query with only provided fields
    fields = {}
    for key, value in update.dict(exclude_unset=True).items():
        if value is not None:
            fields[key] = value

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    fields["updated_at"] = datetime.now().isoformat()

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values())

    conn.execute(f"UPDATE brand_config SET {set_clause} WHERE id = (SELECT MAX(id) FROM brand_config)", values)
    conn.commit()
    conn.close()

    return {"status": "updated", "fields": list(fields.keys())}


@router.post("/logo")
async def upload_logo(file: UploadFile = File(...)):
    """Upload brand logo."""
    UPLOADS_DIR.mkdir(exist_ok=True)
    logo_path = UPLOADS_DIR / f"brand-logo{Path(file.filename).suffix}"
    with open(logo_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Save path in brand config
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "UPDATE brand_config SET logo_path = ?, updated_at = ? WHERE id = (SELECT MAX(id) FROM brand_config)",
        (str(logo_path), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    return {"status": "uploaded", "path": str(logo_path)}


@router.get("/colors")
async def get_brand_colors():
    """Get brand color palette (for image generation)."""
    init_brand_tables()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT primary_color, secondary_color, dark_bg, light_bg, success_color, warning_color, danger_color FROM brand_config ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else {}


@router.get("/image-prompt-context")
async def get_image_prompt_context():
    """Get brand context for enriching image generation prompts."""
    init_brand_tables()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT brand_name, primary_color, secondary_color, dark_bg, tone, forbidden_styles FROM brand_config ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        return {}
    config = dict(row)
    return {
        "brand": config["brand_name"],
        "style_direction": f"Use colors: {config['primary_color']} (primary), {config['secondary_color']} (accent), {config['dark_bg']} (background). Style: modern, clean, professional.",
        "forbidden": config["forbidden_styles"],
        "tone": config["tone"],
    }
