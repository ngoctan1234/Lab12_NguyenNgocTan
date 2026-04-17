"""Redis-backed sliding window rate limiting."""

from __future__ import annotations

import time

from fastapi import Depends, HTTPException

from app.auth import verify_api_key
from app.config import settings
from app.redis_store import redis_client


def check_rate_limit(user_id: str = Depends(verify_api_key)) -> None:
    now = time.time()
    window_start = now - 60
    key = f"rate_limit:{user_id}"

    pipe = redis_client.pipeline(transaction=False)
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, 61)
    _, _, current_count, _ = pipe.execute()

    if current_count > settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
            headers={"Retry-After": "60"},
        )
