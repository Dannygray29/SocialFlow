import base64
import hashlib
import json
import os
import httpx
from cryptography.fernet import Fernet
from fastapi import FastAPI, Request

app = FastAPI()
CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"


def fernet():
    secret = os.getenv("SOCIALFLOW_SECRET_KEY", "")
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())) if secret else None


@app.get("/")
async def status(request: Request):
    value = request.cookies.get("socialflow_youtube")
    f = fernet()
    if not value or not f:
        return {"connected": False}
    try:
        data = json.loads(f.decrypt(value.encode()).decode())
        token = data.get("access_token")
        if not token:
            return {"connected": False}
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(CHANNELS_URL, params={"part": "snippet", "mine": "true"}, headers={"Authorization": f"Bearer {token}"})
        if r.status_code != 200:
            return {"connected": False, "error": "YouTube authorization expired or was revoked"}
        items = r.json().get("items", [])
        if not items:
            return {"connected": False}
        return {"connected": True, "channel_id": items[0].get("id"), "channel_name": items[0].get("snippet", {}).get("title")}
    except Exception:
        return {"connected": False}
