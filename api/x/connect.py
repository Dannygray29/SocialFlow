import base64
import hashlib
import hmac
import os
import secrets
from urllib.parse import urlencode
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

app = FastAPI()
X_AUTHORIZE = "https://x.com/i/oauth2/authorize"
SCOPES = "tweet.read tweet.write users.read offline.access"

def _secret():
    return os.getenv("SOCIALFLOW_SECRET_KEY", "").encode()

def _sign(value):
    return hmac.new(_secret(), value.encode(), hashlib.sha256).hexdigest()

@app.get("/")
async def connect():
    client_id = os.getenv("X_CLIENT_ID", "")
    if not client_id or not _secret():
        raise HTTPException(status_code=503, detail="X OAuth is not configured")
    verifier = secrets.token_urlsafe(64)
    payload = base64.urlsafe_b64encode(verifier.encode()).decode().rstrip("=")
    state = payload + "." + _sign(payload)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    redirect_uri = os.getenv("X_REDIRECT_URI", "https://social-flow-nu.vercel.app/api/x/callback")
    params = {"response_type": "code", "client_id": client_id, "redirect_uri": redirect_uri, "scope": SCOPES, "state": state, "code_challenge": challenge, "code_challenge_method": "S256"}
    return RedirectResponse(X_AUTHORIZE + "?" + urlencode(params), status_code=302)
