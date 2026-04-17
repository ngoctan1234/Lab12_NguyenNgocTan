"""Shared Redis access and conversation storage helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import redis

from app.config import settings


redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def ping_redis() -> bool:
    redis_client.ping()
    return True


def _history_key(session_id: str) -> str:
    return f"history:{session_id}"


def append_message(session_id: str, role: str, content: str) -> None:
    key = _history_key(session_id)
    payload = json.dumps(
        {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    pipe = redis_client.pipeline(transaction=False)
    pipe.rpush(key, payload)
    pipe.ltrim(key, -settings.history_max_messages, -1)
    pipe.expire(key, settings.conversation_ttl_seconds)
    pipe.execute()


def load_history(session_id: str) -> list[dict[str, Any]]:
    entries = redis_client.lrange(_history_key(session_id), 0, -1)
    return [json.loads(entry) for entry in entries]
