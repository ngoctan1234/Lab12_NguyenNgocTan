"""Production-ready AI agent for part 6."""

from __future__ import annotations

import json
import logging
import signal
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import check_budget
from app.rate_limiter import check_rate_limit
from app.redis_store import append_message, load_history, ping_redis
from utils.mock_llm import ask as mock_llm_ask


logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO), format="%(message)s")
logger = logging.getLogger(__name__)

START_TIME = time.time()
INSTANCE_ID = f"agent-{uuid.uuid4().hex[:8]}"
IS_READY = False
IS_SHUTTING_DOWN = False


def log_event(event: str, **fields: object) -> None:
    logger.info(
        json.dumps(
            {
                "event": event,
                "instance_id": INSTANCE_ID,
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                **fields,
            }
        )
    )


def shutdown_handler(signum, frame) -> None:
    global IS_READY, IS_SHUTTING_DOWN
    IS_SHUTTING_DOWN = True
    IS_READY = False
    log_event("sigterm_received", signal=signum)


signal.signal(signal.SIGTERM, shutdown_handler)
if hasattr(signal, "SIGINT"):
    signal.signal(signal.SIGINT, shutdown_handler)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = Field(default=None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global IS_READY
    log_event("startup", app=settings.app_name, version=settings.app_version)
    ping_redis()
    IS_READY = True
    log_event("ready")
    try:
        yield
    finally:
        IS_READY = False
        log_event("shutdown")


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    if IS_SHUTTING_DOWN and request.url.path not in {"/health", "/ready"}:
        return JSONResponse(status_code=503, content={"detail": "Server is shutting down"})

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log_event("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
def health():
    return {
        "status": "ok",
        "instance_id": INSTANCE_ID,
        "uptime_seconds": round(time.time() - START_TIME, 2),
    }


@app.get("/ready")
def ready():
    if not IS_READY or IS_SHUTTING_DOWN:
        return JSONResponse(status_code=503, content={"status": "not ready"})

    try:
        ping_redis()
    except Exception as exc:
        return JSONResponse(status_code=503, content={"status": "not ready", "reason": str(exc)})

    return {"status": "ready", "instance_id": INSTANCE_ID}


@app.post("/ask")
def ask(
    body: AskRequest,
    user_id: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit),
    budget_info: dict = Depends(check_budget),
):
    session_id = body.session_id or user_id

    try:
        history_before = load_history(session_id)
        append_message(session_id, "user", body.question)
        answer = mock_llm_ask(body.question)
        append_message(session_id, "assistant", answer)
        history_after = load_history(session_id)
    except HTTPException:
        raise
    except Exception as exc:
        log_event("ask_failed", user_id=user_id, session_id=session_id, error=str(exc))
        raise HTTPException(status_code=503, detail="Conversation store unavailable") from exc

    log_event(
        "ask_completed",
        user_id=user_id,
        session_id=session_id,
        history_messages=len(history_after),
        estimated_cost_usd=budget_info["estimated_cost_usd"],
    )

    return {
        "answer": answer,
        "session_id": session_id,
        "user_id": user_id,
        "history_length": len(history_after),
        "previous_messages": len(history_before),
        "served_by": INSTANCE_ID,
    }


@app.get("/history/{session_id}")
def get_history(session_id: str, _: str = Depends(verify_api_key)):
    messages = load_history(session_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "messages": messages}
