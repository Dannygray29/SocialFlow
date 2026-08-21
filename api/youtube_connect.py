import hashlib
import hmac
import os
import secrets
from urllib.parse import urlencode
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

app = FastAPI()
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"


def secret():
    return os.getenv("SOCIALFLOW_SECRET_KEY", "").encode()


def sign(value: str) -> str:
    return hmac.new(secret(), value.encode(), hashlib.sha256).hexdigest()


@app.get("/")
async def connect():
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    if not client_id or not secret():
        raise HTTPException(status_code=503, detail="YouTube OAuth is not configured")
    state = secrets.token_urlsafe(32)
    signed = f"{state}.{sign(state)}"
    redirect_uri = os.getenv("YOUTUBE_REDIRECT_URI", "https://social-flow-nu.vercel.app/api/youtube_callback")
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": signed,
    }
    return RedirectResponse(AUTH_URL + "?" + urlencode(params), status_code=302)
