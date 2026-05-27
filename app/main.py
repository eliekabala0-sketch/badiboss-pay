import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_database_url, settings
from app.db.base import Base
from app.db.init_db import seed_default_admin
from app.db.session import SessionLocal, engine
from app.frontend_paths import get_frontend_runtime_state, log_frontend_runtime_state, resolve_frontend_dist
from app.middleware.request_context import request_context_middleware
from app import models  # noqa: F401

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(request_context_middleware)
app.include_router(api_router)

frontend_dist = resolve_frontend_dist()
frontend_index = frontend_dist / "index.html"
frontend_assets = frontend_dist / "assets"

if frontend_assets.exists():
    app.mount("/admin/assets", StaticFiles(directory=frontend_assets), name="admin-assets")


def _database_configured() -> bool:
    return not get_database_url().startswith("sqlite")


def _database_backend() -> str:
    database_url = get_database_url()
    if database_url.startswith("sqlite"):
        return "sqlite"
    if database_url.startswith(("postgresql", "postgres")):
        return "postgresql"
    return "configured"


def _print_startup_diag(startup_ok: bool) -> None:
    lines = [
        f"[startup-diag] cwd={Path.cwd()}",
        f"[startup-diag] frontend_path={frontend_dist}",
        f"[startup-diag] index_exists={'yes' if frontend_index.exists() else 'no'}",
        f"[startup-diag] PORT={os.getenv('PORT') or 'not-set'}",
        f"[startup-diag] startup_ok={'yes' if startup_ok else 'no'}",
        f"[startup-diag] database_configured={'yes' if _database_configured() else 'no'}",
    ]
    for line in lines:
        print(line, flush=True)


def _frontend_unavailable_response():
    state = get_frontend_runtime_state()
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Frontend build not available on this deployment",
            "runtime": state,
        },
    )


@app.get("/admin/runtime-diag")
def admin_runtime_diag():
    state = get_frontend_runtime_state()
    state["database_configured"] = _database_configured()
    state["database_backend"] = _database_backend()
    return state


@app.get("/admin")
def admin_spa_root():
    if frontend_index.exists():
        return FileResponse(frontend_index)
    return _frontend_unavailable_response()


@app.get("/admin/{path:path}")
def admin_spa_path(path: str):
    if path in {"runtime-diag"}:
        return admin_runtime_diag()
    if path.startswith("api"):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    if frontend_index.exists():
        return FileResponse(frontend_index)
    return _frontend_unavailable_response()


@app.on_event("startup")
def on_startup():
    _print_startup_diag(startup_ok=False)
    log_frontend_runtime_state()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_default_admin(db)
    finally:
        db.close()
    _print_startup_diag(startup_ok=True)
