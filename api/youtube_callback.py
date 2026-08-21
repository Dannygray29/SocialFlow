import base64
import hashlib
import hmac
import json
import os
import httpx
from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse

app = FastAPI()
TOKEN_URL = "https://oauth2.googleapis.com/token"
CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"


def secret():
    return os.getenv("SOCIALFLOW_SECRET_KEY", "").encode()


def fernet():
    s = secret()
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(s).digest())) if s else None


def verify_state(state: str):
    try:
        payload, signature = state.rsplit(".", 1)
        if not hmac.compare_digest(signature, hmac.new(secret(), payload.encode(), hashlib.sha256).hexdigest()):
            raise ValueError
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc


@app.get("/")
async def callback(request: Request):
    params = request.query_params
    if params.get("error"):
        return RedirectResponse("/?youtube_error=" + params.get("error"))
    code = params.get("code")
    state = params.get("state")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing YouTube OAuth code or state")
    verify_state(state)

    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    redirect_uri = os.getenv("YOUTUBE_REDIRECT_URI", "https://social-flow-nu.vercel.app/api/youtube_callback")
    f = fernet()
    if not client_id or not client_secret or not f:
        raise HTTPException(status_code=503, detail="YouTube OAuth credentials are not configured")

    async with httpx.AsyncClient(timeout=30) as client:
        token_resp = await client.post(TOKEN_URL, data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        })
        if token_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="YouTube token exchange failed")
        token = token_resp.json()
        access_token = token.get("access_token")
        if not access_token:
            raise HTTPException(status_code=502, detail="Google did not return an access token")

        channel_resp = await client.get(CHANNELS_URL, params={"part": "snippet", "mine": "true"}, headers={"Authorization": f"Bearer {access_token}"})
        if channel_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Could not load YouTube channel")
        items = channel_resp.json().get("items", [])
        if not items:
            raise HTTPException(status_code=400, detail="No YouTube channel is available to this Google account")

    payload = {
        "access_token": token.get("access_token"),
        "refresh_token": token.get("refresh_token"),
        "expires_in": token.get("expires_in"),
        "channel_id": items[0].get("id"),
        "channel_name": items[0].get("snippet", {}).get("title"),
    }
    encrypted = f.encrypt(json.dumps(payload).encode()).decode()
    response = RedirectResponse("/?youtube_connected=true", status_code=302)
    response.set_cookie(
        "socialflow_youtube", encrypted, httponly=True, secure=True,
        samesite="lax", max_age=60 * 60 * 24 * 180, path="/"
    )
    return response
