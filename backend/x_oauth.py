"""X OAuth 2.0 Authorization Code + PKCE routes for SocialFlow."""
import base64
import hashlib
import hmac
import os
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/api/x", tags=["x"])

X_AUTHORIZE = "https://twitter.com/i/oauth2/authorize"
X_TOKEN = "https://api.x.com/2/oauth2/token"
SCOPES = "tweet.read tweet.write users.read offline.access"


def _secret() -> bytes:
    return os.getenv("SOCIALFLOW_SECRET_KEY", "").encode()


def _sign(value: str) -> str:
    return hmac.new(_secret(), value.encode(), hashlib.sha256).hexdigest()


def _state(verifier: str) -> str:
    payload = base64.urlsafe_b64encode(verifier.encode()).decode().rstrip("=")
    return payload + "." + _sign(payload)


def _verify_state(state: str) -> str:
    try:
        payload, signature = state.split(".", 1)
        if not hmac.compare_digest(signature, _sign(payload)):
            raise ValueError
        padding = "=" * (-len(payload) % 4)
        return base64.urlsafe_b64decode(payload + padding).decode()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc


def _callback_url() -> str:
    return os.getenv("X_REDIRECT_URI", "https://social-flow-nu.vercel.app/api/x/callback")


@router.get("/connect")
async def x_connect():
    client_id = os.getenv("X_CLIENT_ID", "")
    if not client_id:
        raise HTTPException(status_code=503, detail="X_CLIENT_ID is not configured")
    if not _secret():
        raise HTTPException(status_code=503, detail="SOCIALFLOW_SECRET_KEY is not configured")

    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = _state(verifier)
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": _callback_url(),
        "scope": SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    return RedirectResponse(X_AUTHORIZE + "?" + urlencode(params))


@router.get("/callback")
async def x_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        return RedirectResponse(f"/?x_error={error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth code or state")

    verifier = _verify_state(state)
    client_id = os.getenv("X_CLIENT_ID", "")
    client_secret = os.getenv("X_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise HTTPException(status_code=503, detail="X OAuth credentials are not configured")

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            X_TOKEN,
            data={
                "code": code,
                "grant_type": "authorization_code",
                "client_id": client_id,
                "redirect_uri": _callback_url(),
                "code_verifier": verifier,
            },
            auth=(client_id, client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="X token exchange failed")

    token = response.json()
    # Deliberately do not return access/refresh tokens in the browser URL.
    # Persistent token storage will be wired to the SocialFlow Supabase project.
    return RedirectResponse(f"/?x_connected=true&scope={token.get('scope', '')}")
