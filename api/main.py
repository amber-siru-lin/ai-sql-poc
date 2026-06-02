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
from src.chat_sessions.routes import router as chat_sessions_router
from src.chat_sessions.store import init_chat_sessions_from_env, sessions_available, shutdown_chat_sessions
from src.check_setup import check_all
from src.postgres_docker_status import postgres_docker_status
from src.semantic_editor.ag_ui_agent import SemanticEditorLangGraphAgent
from src.semantic_editor.agent import (
    EDITOR_AGENT_DESCRIPTION,
    EDITOR_AGENT_NAME,
    build_editor_agent_graph,
)
from src.semantic_editor import (
    SemanticPathError,
    SemanticPrError,
    build_consumers_response,
    build_pr_draft,
    create_semantic_pr,
    github_config,
    list_semantic_files,
    read_semantic_file,
    run_wren_validate,
    write_semantic_file,
)
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

app.include_router(chat_sessions_router)


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
    source: str | None = None,
):
    """List query audit records from S3 (newest first)."""
    src = source if source and source.lower() != "all" else None
    return {
        "audit": audit_config(),
        "dates": list_audit_dates(),
        "entries": read_audit_entries(
            date=date,
            limit=limit,
            thread_id=thread_id,
            source=src,
        ),
    }


@app.get("/api/audit/sessions")
def audit_sessions(limit: int = 30, source: str | None = "api"):
    """List sessions grouped by thread_id (from audit log)."""
    src = source if source and source.lower() != "all" else None
    return {
        "audit": audit_config(),
        "sessions": list_audit_sessions(limit=limit, source=src),
    }


@app.get("/api/semantic/consumers")
def semantic_consumers():
    """Manifest of runtime consumers and git paths for the semantic layer editor."""
    status_block = _semantic_layer_status()
    return build_consumers_response(status_block)


@app.get("/api/semantic/tree")
def semantic_tree(root: str | None = None):
    """List editable semantic layer files under allowlisted roots."""
    try:
        return list_semantic_files(root=root)
    except SemanticPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/semantic/file")
def semantic_file_get(path: str):
    """Read one allowlisted semantic layer file."""
    try:
        return read_semantic_file(path)
    except SemanticPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"not found: {path}") from exc


class SemanticFileWriteRequest(BaseModel):
    content: str


@app.put("/api/semantic/file")
def semantic_file_put(path: str, body: SemanticFileWriteRequest):
    """Write one allowlisted semantic layer file."""
    try:
        return write_semantic_file(path, body.content)
    except SemanticPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/semantic/validate")
def semantic_validate():
    """Run ``wren context validate`` for wren/tpch."""
    return run_wren_validate()


@app.get("/api/semantic/pr/config")
def semantic_pr_config():
    """GitHub PR settings (token presence only — never returns the token)."""
    return github_config()


@app.get("/api/semantic/pr/draft")
def semantic_pr_draft(
    paths: str | None = None,
    base_branch: str | None = None,
):
    """Suggest PR title/body from current semantic layer diffs."""
    path_list = [p.strip() for p in paths.split(",") if p.strip()] if paths else None
    try:
        return build_pr_draft(paths=path_list, base_branch=base_branch)
    except SemanticPrError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class SemanticPrCreateRequest(BaseModel):
    title: str
    body: str
    paths: list[str] | None = None
    base_branch: str | None = None
    branch_name: str | None = None
    audit_entry_ids: list[str] | None = None
    require_validate: bool = True


@app.post("/api/semantic/pr")
def semantic_pr_create(body: SemanticPrCreateRequest):
    """Commit allowlisted semantic changes and open a GitHub pull request."""
    try:
        return create_semantic_pr(
            title=body.title,
            body=body.body,
            paths=body.paths,
            base_branch=body.base_branch,
            branch_name=body.branch_name,
            audit_entry_ids=body.audit_entry_ids,
            require_validate=body.require_validate,
        )
    except SemanticPrError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/status")
def status():
    """Lightweight status for the UI header (does not invoke the agent)."""
    return {
        "status": "ok",
        "agent": AGENT_NAME,
        "dataset": "TPCH_SF1",
        "semantic_layer": _semantic_layer_status(),
        "audit": audit_config(check_s3=True),
        "postgres": postgres_docker_status(),
        "checkpoint": {
            "backend": checkpoint_backend(),
            "database_url_configured": bool(os.environ.get("DATABASE_URL", "").strip()),
        },
        "sessions": {
            "backend": "postgres" if sessions_available() else "memory",
            "available": sessions_available(),
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
async def startup() -> None:
    check_all()
    await init_checkpointer_from_env()
    await init_chat_sessions_from_env()
    from src.checkpoint_factory import get_checkpointer

    graph = build_agent_graph(DEFAULT_SEMANTIC_LAYER, checkpointer=get_checkpointer())
    agent = SemanticLayerLangGraphAgent(
        name=AGENT_NAME,
        description=AGENT_DESCRIPTION,
        graph=graph,
    )
    add_langgraph_fastapi_endpoint(app, agent, path="/")

    editor_graph = build_editor_agent_graph(checkpointer=get_checkpointer())
    editor_agent = SemanticEditorLangGraphAgent(
        name=EDITOR_AGENT_NAME,
        description=EDITOR_AGENT_DESCRIPTION,
        graph=editor_graph,
    )
    add_langgraph_fastapi_endpoint(app, editor_agent, path="/semantic-agent")


@app.on_event("shutdown")
async def shutdown() -> None:
    await shutdown_chat_sessions()
    await shutdown_checkpointer()
