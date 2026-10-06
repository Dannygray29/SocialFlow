"""
Inferno social publishing connections.

One-tap UX:
  GET /api/inferno/connections
  GET /api/inferno/connect/youtube
  GET /api/inferno/connect/tiktok
  GET /api/inferno/oauth/{provider}/callback

Secrets and refresh tokens stay server-side and are encrypted with SocialFlow's
existing Fernet key. The browser only sees connection status/account name.
"""
import base64
import hashlib
import json
import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/api/inferno", tags=["Inferno Connections"])

DB_PATH = "socialflow.db"

YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
TIKTOK_SCOPES = "user.info.basic,video.publish"


def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS inferno_connections (
            provider TEXT PRIMARY KEY,
            access_token_encrypted TEXT NOT NULL,
            refresh_token_encrypted TEXT,
            account_name TEXT,
            account_id TEXT,
            expires_at TEXT,
            scopes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def _crypto():
    # Import lazily to avoid circular imports during app startup.
    from main import encrypt, decrypt
    return encrypt, decrypt


def _cfg(name):
    return os.getenv(name, "").strip()


def _redirect_base():
    return _cfg("INFERNO_PUBLIC_BASE_URL").rstrip("/")


def _require_base():
    base = _redirect_base()
    if not base:
        raise HTTPException(
            status_code=503,
            detail="Inferno publishing is not configured yet: INFERNO_PUBLIC_BASE_URL is missing."
        )
    return base


def _save(provider, access_token, refresh_token, account_name, account_id, expires_at, scopes):
    encrypt, _ = _crypto()
    conn = _db()
    conn.execute(
        """INSERT INTO inferno_connections
           (provider, access_token_encrypted, refresh_token_encrypted, account_name,
            account_id, expires_at, scopes, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(provider) DO UPDATE SET
             access_token_encrypted=excluded.access_token_encrypted,
             refresh_token_encrypted=excluded.refresh_token_encrypted,
             account_name=excluded.account_name,
             account_id=excluded.account_id,
             expires_at=excluded.expires_at,
             scopes=excluded.scopes,
             updated_at=CURRENT_TIMESTAMP""",
        (provider, encrypt(access_token), encrypt(refresh_token) if refresh_token else None,
         account_name, account_id, expires_at, scopes),
    )
    conn.commit()
    conn.close()


def _get(provider):
    _, decrypt = _crypto()
    conn = _db()
    row = conn.execute("SELECT * FROM inferno_connections WHERE provider=?", (provider,)).fetchone()
    conn.close()
    if not row:
        return None
    item = dict(row)
    item["access_token"] = decrypt(item.pop("access_token_encrypted"))
    item["refresh_token"] = decrypt(item["refresh_token_encrypted"]) if item["refresh_token_encrypted"] else None
    item.pop("refresh_token_encrypted", None)
    return item


def _state(provider):
    state = secrets.token_urlsafe(32)
    conn = _db()
    conn.execute("CREATE TABLE IF NOT EXISTS inferno_oauth_states (state TEXT PRIMARY KEY, provider TEXT, created_at TEXT)")
    conn.execute("INSERT INTO inferno_oauth_states VALUES (?, ?, ?)", (state, provider, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return state


def _consume_state(state, provider):
    conn = _db()
    row = conn.execute("SELECT * FROM inferno_oauth_states WHERE state=? AND provider=?", (state, provider)).fetchone()
    conn.execute("DELETE FROM inferno_oauth_states WHERE state=?", (state,))
    conn.commit()
    conn.close()
    if not row:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state.")
    created = datetime.fromisoformat(row["created_at"])
    if datetime.utcnow() - created > timedelta(minutes=10):
        raise HTTPException(status_code=400, detail="OAuth session expired. Please connect again.")


@router.get("/connections")
async def connections():
    result = {}
    for provider in ("youtube", "tiktok"):
        row = _get(provider)
        result[provider] = {
            "connected": bool(row),
            "account_name": row.get("account_name") if row else None,
            "account_id": row.get("account_id") if row else None,
        }
    return result


@router.get("/connect/youtube")
async def connect_youtube():
    client_id = _cfg("YOUTUBE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=503, detail="YOUTUBE_CLIENT_ID is not configured.")
    redirect_uri = _require_base() + "/api/inferno/oauth/youtube/callback"
    state = _state("youtube")
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": YOUTUBE_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return RedirectResponse("https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params))


@router.get("/connect/tiktok")
async def connect_tiktok():
    client_key = _cfg("TIKTOK_CLIENT_KEY")
    if not client_key:
        raise HTTPException(status_code=503, detail="TIKTOK_CLIENT_KEY is not configured.")
    redirect_uri = _require_base() + "/api/inferno/oauth/tiktok/callback"
    state = _state("tiktok")
    params = {
        "client_key": client_key,
        "response_type": "code",
        "scope": TIKTOK_SCOPES,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    return RedirectResponse("https://www.tiktok.com/v2/auth/authorize/?" + urlencode(params))


@router.get("/oauth/youtube/callback")
async def youtube_callback(code: str = "", state: str = "", error: str = ""):
    if error:
        raise HTTPException(status_code=400, detail=f"YouTube authorization failed: {error}")
    _consume_state(state, "youtube")
    redirect_uri = _require_base() + "/api/inferno/oauth/youtube/callback"
    async with httpx.AsyncClient(timeout=30) as client:
        token = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": _cfg("YOUTUBE_CLIENT_ID"),
                "client_secret": _cfg("YOUTUBE_CLIENT_SECRET"),
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token.status_code != 200:
            raise HTTPException(status_code=502, detail="YouTube token exchange failed.")
        data = token.json()
        access = data.get("access_token")
        refresh = data.get("refresh_token")
        if not access:
            raise HTTPException(status_code=502, detail="YouTube did not return an access token.")

        channel = await client.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "snippet", "mine": "true"},
            headers={"Authorization": f"Bearer {access}"},
        )
        channel_data = channel.json() if channel.status_code == 200 else {}
        item = (channel_data.get("items") or [{}])[0]
        snippet = item.get("snippet") or {}
        expires = (datetime.utcnow() + timedelta(seconds=int(data.get("expires_in", 3600)))).isoformat()
        _save("youtube", access, refresh, snippet.get("title") or "YouTube channel",
              item.get("id"), expires, YOUTUBE_SCOPE)

    return RedirectResponse("/inferno?connected=youtube")


@router.get("/oauth/tiktok/callback")
async def tiktok_callback(code: str = "", state: str = "", error: str = ""):
    if error:
        raise HTTPException(status_code=400, detail=f"TikTok authorization failed: {error}")
    _consume_state(state, "tiktok")
    redirect_uri = _require_base() + "/api/inferno/oauth/tiktok/callback"
    async with httpx.AsyncClient(timeout=30) as client:
        token = await client.post(
            "https://open.tiktokapis.com/v2/oauth/token/",
            data={
                "client_key": _cfg("TIKTOK_CLIENT_KEY"),
                "client_secret": _cfg("TIKTOK_CLIENT_SECRET"),
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token.status_code != 200:
            raise HTTPException(status_code=502, detail="TikTok token exchange failed.")
        data = token.json()
        access = data.get("access_token")
        refresh = data.get("refresh_token")
        open_id = data.get("open_id")
        if not access:
            raise HTTPException(status_code=502, detail="TikTok did not return an access token.")

        profile = await client.get(
            "https://open.tiktokapis.com/v2/user/info/",
            params={"fields": "display_name,avatar_url,open_id"},
            headers={"Authorization": f"Bearer {access}"},
        )
        pdata = profile.json() if profile.status_code == 200 else {}
        user = pdata.get("data", {}).get("user", {})
        expires = (datetime.utcnow() + timedelta(seconds=int(data.get("expires_in", 86400)))).isoformat()
        _save("tiktok", access, refresh, user.get("display_name") or "TikTok account",
              user.get("open_id") or open_id, expires, TIKTOK_SCOPES)

    return RedirectResponse("/inferno?connected=tiktok")
