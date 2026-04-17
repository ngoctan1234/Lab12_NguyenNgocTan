"""API key authentication helpers."""

from fastapi import Header, HTTPException

from app.config import settings


def verify_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> str:
    if x_api_key != settings.agent_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_user_id or "default-user"
