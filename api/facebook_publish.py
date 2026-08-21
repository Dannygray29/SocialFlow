import base64
import hashlib
import json
import os
import httpx
from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

app = FastAPI()
GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v25.0")
GRAPH = f"https://graph.facebook.com/{GRAPH_VERSION}"


def fernet():
    secret = os.getenv("SOCIALFLOW_SECRET_KEY", "")
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())) if secret else None


class PublishRequest(BaseModel):
    message: str
    link: str | None = None


@app.post("/")
async def publish(request: Request, body: PublishRequest):
    value = request.cookies.get("socialflow_facebook")
    f = fernet()
    if not value or not f:
        raise HTTPException(status_code=401, detail="Facebook Page is not connected")
    try:
        data = json.loads(f.decrypt(value.encode()).decode())
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Facebook connection is invalid") from exc

    params = {"message": body.message, "access_token": data["page_access_token"]}
    if body.link:
        params["link"] = body.link
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{GRAPH}/{data['page_id']}/feed", data=params)
    if r.status_code not in (200, 201):
        raise HTTPException(status_code=r.status_code, detail=r.text[:500])
    return {"success": True, "platform": "facebook", "result": r.json()}
