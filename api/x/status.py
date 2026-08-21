import base64
import hashlib
import json
import os
import httpx
from cryptography.fernet import Fernet
from fastapi import Request


def _fernet():
    secret = os.getenv("SOCIALFLOW_SECRET_KEY", "")
    if not secret:
        return None
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest()))


def handler(request: Request):
    value = request.cookies.get("socialflow_x_token")
    f = _fernet()
    if not value or not f:
        return {"connected": False}
    try:
        token = json.loads(f.decrypt(value.encode()).decode())
        access_token = token.get("access_token")
        if not access_token:
            return {"connected": False}
        with httpx.Client(timeout=20) as client:
            response = client.get(
                "https://api.x.com/2/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if response.status_code != 200:
            return {"connected": False, "error": "X authorization expired or was revoked"}
        data = response.json().get("data", {})
        return {"connected": True, "username": data.get("username"), "name": data.get("name"), "id": data.get("id")}
    except Exception:
        return {"connected": False}
