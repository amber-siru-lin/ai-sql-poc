"""FastAPI server — AG-UI bridge to the Phase 2 Deep Agent."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.agent_factory import AGENT_DESCRIPTION, AGENT_NAME, build_agent_graph
from src.check_setup import check_all

DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

DEV_ORIGIN_REGEX = r"http://(localhost|127\.0\.0\.1):\d+"

app = FastAPI(title="AI SQL POC API", version="0.1.0")

_cors_origins = os.environ.get("CORS_ORIGINS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins.split(",") if _cors_origins else DEFAULT_ORIGINS,
    allow_origin_regex=None if _cors_origins else DEV_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status")
def status():
    """Lightweight status for the UI header (does not invoke the agent)."""
    return {
        "status": "ok",
        "agent": AGENT_NAME,
        "dataset": "TPCH_SF1",
    }


def copilotkit_runtime_info() -> dict:
    """Minimal CopilotKit /info payload.

    Empty ``agents`` keeps chat on the local HttpAgent (AG-UI at ``/``) instead of
    registering a proxied runtime agent that would conflict with AG-UI protocol.
    """
    return {"version": "0.1.0", "agents": {}}


class CopilotKitMethodRequest(BaseModel):
    method: str


@app.get("/copilotkit/info")
def copilotkit_info_get():
    return copilotkit_runtime_info()


@app.post("/copilotkit")
async def copilotkit_single_endpoint(body: CopilotKitMethodRequest):
    """CopilotKit single-endpoint transport (POST with ``{\"method\": \"info\"}``)."""
    if body.method == "info":
        return copilotkit_runtime_info()
    raise HTTPException(status_code=400, detail=f"Unsupported method: {body.method}")


@app.on_event("startup")
def startup() -> None:
    check_all()
    graph = build_agent_graph()
    agent = LangGraphAgent(
        name=AGENT_NAME,
        description=AGENT_DESCRIPTION,
        graph=graph,
    )
    add_langgraph_fastapi_endpoint(app, agent, path="/")
