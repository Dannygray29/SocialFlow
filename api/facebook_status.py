import base64
import hashlib
import json
import os
import httpx
from cryptography.fernet import Fernet
from fastapi import FastAPI, Request

app = FastAPI()
GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v25.0")
GRAPH = f"https://graph.facebook.com/{GRAPH_VERSION}"


def fernet():
    secret = os.getenv("SOCIALFLOW_SECRET_KEY", "")
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())) if secret else None


@app.get("/")
async def status(request: Request):
    value = request.cookies.get("socialflow_facebook")
    f = fernet()
    if not value or not f:
        return {"connected": False}
    try:
        data = json.loads(f.decrypt(value.encode()).decode())
        token = data.get("page_access_token")
        page_id = data.get("page_id")
        if not token or not page_id:
            return {"connected": False}
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{GRAPH}/{page_id}", params={"fields": "id,name", "access_token": token})
        if r.status_code != 200:
            return {"connected": False, "error": "Facebook authorization expired or was revoked"}
        page = r.json()
        return {"connected": True, "page_id": page.get("id"), "page_name": page.get("name")}
    except Exception:
        return {"connected": False}
