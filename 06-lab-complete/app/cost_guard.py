"""Redis-backed monthly budget guard."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request

from app.auth import verify_api_key
from app.config import settings
from app.redis_store import redis_client


PRICE_PER_1K_INPUT_TOKENS = 0.00015
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006


def estimate_cost_usd(question: str) -> float:
    approx_input_tokens = max(1, len(question.split()) * 1.3)
    approx_output_tokens = max(40, len(question.split()) * 2.5)
    input_cost = (approx_input_tokens / 1000) * PRICE_PER_1K_INPUT_TOKENS
    output_cost = (approx_output_tokens / 1000) * PRICE_PER_1K_OUTPUT_TOKENS
    return round(input_cost + output_cost, 6)


async def check_budget(
    request: Request,
    user_id: str = Depends(verify_api_key),
) -> dict:
    body = await request.json()
    question = body.get("question", "")
    estimated_cost = estimate_cost_usd(question)

    month_key = datetime.now(timezone.utc).strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    current_spend = float(redis_client.get(key) or 0.0)

    if current_spend + estimated_cost > settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Monthly budget exceeded",
                "used_usd": round(current_spend, 6),
                "budget_usd": settings.monthly_budget_usd,
            },
        )

    pipe = redis_client.pipeline(transaction=False)
    pipe.incrbyfloat(key, estimated_cost)
    pipe.expire(key, 32 * 24 * 3600)
    pipe.execute()

    return {"estimated_cost_usd": estimated_cost, "current_spend_usd": current_spend}
