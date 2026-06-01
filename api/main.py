"""FastAPI server — AG-UI bridge to the Phase 2 Deep Agent."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_dotenv() -> None:
    """Load ROOT/.env into os.environ (does not override existing vars)."""
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()

from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.ag_ui_agent import SemanticLayerLangGraphAgent
from src.agent_factory import AGENT_DESCRIPTION, AGENT_NAME, build_agent_graph
from src.audit_logger import audit_config
from src.audit_reader import list_audit_dates, list_audit_sessions, read_audit_entries
from src.checkpoint_factory import checkpoint_backend, init_checkpointer_from_env, shutdown_checkpointer
from src.check_setup import check_all
from src.semantic_editor import build_consumers_response
from src.semantic_layer.types import SEMANTIC_LAYER_MODES, DEFAULT_SEMANTIC_LAYER
from src.tools.cortex_tools import cortex_ready
from src.tools.wren_tools import wren_ready

DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

DEV_ORIGIN_REGEX = r"http://(localhost|127\.0\.0\.1):\d+"

app = FastAPI(title="AI SQL POC API", version="0.2.0")

_cors_origins = os.environ.get("CORS_ORIGINS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins.split(",") if _cors_origins else DEFAULT_ORIGINS,
    allow_origin_regex=None if _cors_origins else DEV_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _semantic_layer_status() -> dict:
    wren_ok, wren_msg = wren_ready()
    cortex_ok, cortex_msg = cortex_ready()
    return {
        "default": DEFAULT_SEMANTIC_LAYER,
        "modes": list(SEMANTIC_LAYER_MODES),
        "wren_ready": wren_ok,
        "wren_message": wren_msg,
        "cortex_ready": cortex_ok,
        "cortex_message": cortex_msg,
    }


@app.get("/api/audit/logs")
def audit_logs(
    date: str | None = None,
    limit: int = 50,
    thread_id: str | None = None,
):
    """List query audit records from S3 (newest first)."""
    return {
        "audit": audit_config(),
        "dates": list_audit_dates(),
        "entries": read_audit_entries(date=date, limit=limit, thread_id=thread_id),
    }


@app.get("/api/audit/sessions")
def audit_sessions(limit: int = 30):
    """List chat sessions grouped by thread_id (from audit log)."""
    return {
        "audit": audit_config(),
        "sessions": list_audit_sessions(limit=limit),
    }


@app.get("/api/semantic/consumers")
def semantic_consumers():
    """Manifest of runtime consumers and git paths for the semantic layer editor."""
    status_block = _semantic_layer_status()
    return build_consumers_response(status_block)


@app.get("/api/status")
def status():
    """Lightweight status for the UI header (does not invoke the agent)."""
    return {
        "status": "ok",
        "agent": AGENT_NAME,
        "dataset": "TPCH_SF1",
        "semantic_layer": _semantic_layer_status(),
        "audit": audit_config(check_s3=True),
        "checkpoint": {
            "backend": checkpoint_backend(),
            "database_url_configured": bool(os.environ.get("DATABASE_URL", "").strip()),
        },
    }


def copilotkit_runtime_info() -> dict:
    """Minimal CopilotKit /info payload.

    Empty ``agents`` keeps chat on the local HttpAgent (AG-UI at ``/``) instead of
    registering a proxied runtime agent that would conflict with AG-UI protocol.
    """
    return {"version": "0.2.0", "agents": {}}


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
    init_checkpointer_from_env()
    from src.checkpoint_factory import get_checkpointer

    graph = build_agent_graph(DEFAULT_SEMANTIC_LAYER, checkpointer=get_checkpointer())
    agent = SemanticLayerLangGraphAgent(
        name=AGENT_NAME,
        description=AGENT_DESCRIPTION,
        graph=graph,
    )
    add_langgraph_fastapi_endpoint(app, agent, path="/")


@app.on_event("shutdown")
def shutdown() -> None:
    shutdown_checkpointer()
