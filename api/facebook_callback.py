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
GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v25.0")
GRAPH = f"https://graph.facebook.com/{GRAPH_VERSION}"


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
        return payload
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc


@app.get("/")
async def callback(request: Request):
    params = request.query_params
    if params.get("error"):
        return RedirectResponse("/?facebook_error=" + params.get("error"))
    code = params.get("code")
    state = params.get("state")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing Facebook OAuth code or state")
    verify_state(state)

    app_id = os.getenv("META_APP_ID", "")
    app_secret = os.getenv("META_APP_SECRET", "")
    redirect_uri = os.getenv("META_REDIRECT_URI", "https://social-flow-nu.vercel.app/api/facebook_callback")
    if not app_id or not app_secret or not fernet():
        raise HTTPException(status_code=503, detail="Facebook OAuth credentials are not configured")

    async with httpx.AsyncClient(timeout=30) as client:
        token_resp = await client.get(f"{GRAPH}/oauth/access_token", params={
            "client_id": app_id,
            "client_secret": app_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        })
        if token_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Facebook token exchange failed")
        user_token = token_resp.json().get("access_token")
        if not user_token:
            raise HTTPException(status_code=502, detail="Facebook did not return an access token")

        pages_resp = await client.get(f"{GRAPH}/me/accounts", params={
            "fields": "id,name,access_token",
            "access_token": user_token,
        })
        if pages_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Could not load Facebook Pages")
        pages = pages_resp.json().get("data", [])
        if not pages:
            raise HTTPException(status_code=400, detail="No Facebook Pages are available to this account")

    # Keep the selected Page token server-side in an encrypted HttpOnly cookie.
    selected = pages[0]
    payload = {
        "page_id": selected.get("id"),
        "page_name": selected.get("name"),
        "page_access_token": selected.get("access_token"),
    }
    encrypted = fernet().encrypt(json.dumps(payload).encode()).decode()
    response = RedirectResponse("/?facebook_connected=true", status_code=302)
    response.set_cookie(
        "socialflow_facebook", encrypted, httponly=True, secure=True,
        samesite="lax", max_age=60 * 60 * 24 * 60, path="/"
    )
    return response
