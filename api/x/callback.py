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
X_TOKEN = "https://api.x.com/2/oauth2/token"

def _secret():
    return os.getenv("SOCIALFLOW_SECRET_KEY", "").encode()

def _fernet():
    if not _secret():
        return None
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(_secret()).digest()))

def _verify_state(state):
    try:
        payload, signature = state.split(".", 1)
        expected = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        padding = "=" * (-len(payload) % 4)
        return base64.urlsafe_b64decode(payload + padding).decode()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc

@app.get("/")
async def callback(request: Request):
    params = request.query_params
    error = params.get("error")
    if error:
        return RedirectResponse("/?x_error=" + error, status_code=302)
    code = params.get("code")
    state = params.get("state")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth code or state")
    verifier = _verify_state(state)
    client_id = os.getenv("X_CLIENT_ID", "")
    client_secret = os.getenv("X_CLIENT_SECRET", "")
    redirect_uri = os.getenv("X_REDIRECT_URI", "https://social-flow-nu.vercel.app/api/x/callback")
    if not client_id or not client_secret or not _fernet():
        raise HTTPException(status_code=503, detail="X OAuth credentials are not configured")
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            X_TOKEN,
            data={"code": code, "grant_type": "authorization_code", "redirect_uri": redirect_uri, "code_verifier": verifier},
            auth=(client_id, client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="X token exchange failed")
    token = response.json()
    encrypted = _fernet().encrypt(json.dumps(token).encode()).decode()
    result = RedirectResponse("/?x_connected=true", status_code=302)
    result.set_cookie("socialflow_x_token", encrypted, httponly=True, secure=True, samesite="lax", max_age=60 * 60 * 24 * 180, path="/")
    return result
