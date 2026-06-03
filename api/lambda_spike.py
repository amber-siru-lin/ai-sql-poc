"""Minimal FastAPI app for Lambda / Function URL spike (Unit 2).

Full agent wiring uses ``api.main:app`` in the container image (Unit 7).
"""

from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI(title="AI SQL POC API (Lambda spike)", version="0.2.0-spike")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status")
async def api_status() -> dict:
    return {
        "status": "ok",
        "agent": "nl2sql_assistant",
        "dataset": "tpch_sf1",
        "mode": "lambda_spike",
        "semantic_layer": {
            "default": "off",
            "modes": ["off", "wren", "cortex"],
            "wren_ready": False,
            "wren_message": "Wren not loaded in spike image",
            "cortex_ready": False,
            "cortex_message": "Cortex not loaded in spike image",
        },
        "checkpoint": {"backend": "memory"},
        "sessions": {"backend": "unavailable", "available": False},
    }


@app.get("/copilotkit/info")
async def copilotkit_info() -> dict:
    return {"version": "0.2.0", "agents": {}}


@app.post("/copilotkit")
async def copilotkit_post(body: dict | None = None) -> dict:
    if body and body.get("method") == "info":
        return await copilotkit_info()
    return {"error": "unsupported_method"}


async def _sse_demo() -> AsyncIterator[str]:
    for event in (
        {"type": "RUN_STARTED"},
        {"type": "TEXT_MESSAGE_CHUNK", "delta": "Lambda spike SSE OK"},
        {"type": "RUN_FINISHED"},
    ):
        yield f"data: {json.dumps(event)}\n\n"


@app.post("/")
async def agui_spike() -> StreamingResponse:
    """Placeholder AG-UI root — proves streaming from Function URL."""
    return StreamingResponse(_sse_demo(), media_type="text/event-stream")
