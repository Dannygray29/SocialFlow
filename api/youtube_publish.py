import base64
import hashlib
import json
import os
import httpx
from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form

app = FastAPI()
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
TOKEN_URL = "https://oauth2.googleapis.com/token"


def fernet():
    secret = os.getenv("SOCIALFLOW_SECRET_KEY", "")
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())) if secret else None


async def get_access_token(data: dict) -> str:
    if data.get("access_token"):
        return data["access_token"]
    refresh = data.get("refresh_token")
    if not refresh:
        raise HTTPException(status_code=401, detail="YouTube connection has no refresh token")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(TOKEN_URL, data={
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "refresh_token": refresh,
            "grant_type": "refresh_token",
        })
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Could not refresh YouTube authorization")
    return r.json()["access_token"]


@app.post("/")
async def publish(request: Request, file: UploadFile = File(...), title: str = Form(...), description: str = Form(""), privacy_status: str = Form("private")):
    value = request.cookies.get("socialflow_youtube")
    f = fernet()
    if not value or not f:
        raise HTTPException(status_code=401, detail="YouTube is not connected")
    try:
        data = json.loads(f.decrypt(value.encode()).decode())
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid YouTube connection") from exc

    if privacy_status not in {"private", "unlisted", "public"}:
        raise HTTPException(status_code=400, detail="Invalid privacy status")
    content = await file.read()
    token = await get_access_token(data)
    metadata = {
        "snippet": {"title": title[:100], "description": description[:5000]},
        "status": {"privacyStatus": privacy_status},
    }
    import json as _json
    boundary = "socialflow-boundary"
    body = (
        f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
        + _json.dumps(metadata)
        + f"\r\n--{boundary}\r\nContent-Type: {file.content_type or 'video/mp4'}\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()

    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            UPLOAD_URL,
            params={"uploadType": "multipart", "part": "snippet,status"},
            headers={"Authorization": f"Bearer {token}", "Content-Type": f"multipart/related; boundary={boundary}"},
            content=body,
        )
    if r.status_code not in (200, 201):
        raise HTTPException(status_code=r.status_code, detail=r.text[:1000])
    return {"success": True, "platform": "youtube", "video": r.json()}
