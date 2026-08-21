import hashlib
import hmac
import os
import secrets
from urllib.parse import urlencode
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

app = FastAPI()
GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v25.0")
AUTH_URL = f"https://www.facebook.com/{GRAPH_VERSION}/dialog/oauth"
SCOPES = "pages_show_list,pages_read_engagement,pages_manage_posts"


def secret():
    return os.getenv("SOCIALFLOW_SECRET_KEY", "").encode()


def sign(value: str) -> str:
    return hmac.new(secret(), value.encode(), hashlib.sha256).hexdigest()


@app.get("/")
async def connect():
    client_id = os.getenv("META_APP_ID", "")
    if not client_id or not secret():
        raise HTTPException(status_code=503, detail="Facebook OAuth is not configured")
    state = secrets.token_urlsafe(32)
    signed = f"{state}.{sign(state)}"
    redirect_uri = os.getenv("META_REDIRECT_URI", "https://social-flow-nu.vercel.app/api/facebook_callback")
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": signed,
        "scope": SCOPES,
        "response_type": "code",
    }
    return RedirectResponse(AUTH_URL + "?" + urlencode(params), status_code=302)
