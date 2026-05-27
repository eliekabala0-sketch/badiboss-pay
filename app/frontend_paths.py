import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger("badiboss.frontend")


def _candidate_dist_paths() -> List[Path]:
    app_root = Path(__file__).resolve().parents[1]
    return [
        app_root / "frontend" / "dist",
        Path.cwd() / "frontend" / "dist",
        Path("/app") / "frontend" / "dist",
    ]


def get_frontend_runtime_state() -> Dict[str, Any]:
    candidates = _candidate_dist_paths()
    chosen = candidates[0]
    for candidate in candidates:
        if (candidate / "index.html").exists():
            chosen = candidate
            break

    index_path = chosen / "index.html"
    assets_path = chosen / "assets"
    assets_files: List[str] = []
    if assets_path.exists() and assets_path.is_dir():
        assets_files = sorted(p.name for p in assets_path.iterdir())[:20]

    parent_listings: Dict[str, List[str]] = {}
    for label, base in [
        ("app_root", Path(__file__).resolve().parents[1]),
        ("cwd", Path.cwd()),
        ("frontend_dir", Path(__file__).resolve().parents[1] / "frontend"),
    ]:
        if base.exists() and base.is_dir():
            parent_listings[label] = sorted(p.name for p in base.iterdir())[:40]

    return {
        "cwd": str(Path.cwd()),
        "app_file": str(Path(__file__).resolve()),
        "candidate_paths": [str(p) for p in candidates],
        "chosen_frontend_dist": str(chosen),
        "frontend_dist_exists": chosen.exists(),
        "index_path": str(index_path),
        "index_exists": index_path.exists(),
        "assets_path": str(assets_path),
        "assets_exists": assets_path.exists(),
        "assets_files": assets_files,
        "parent_listings": parent_listings,
        "env_railway": os.getenv("RAILWAY_ENVIRONMENT"),
        "env_port": os.getenv("PORT"),
    }


def resolve_frontend_dist() -> Path:
    state = get_frontend_runtime_state()
    return Path(state["chosen_frontend_dist"])


def log_frontend_runtime_state() -> None:
    state = get_frontend_runtime_state()
    lines = [
        "=== Badiboss Pay frontend runtime diagnostic ===",
        f"cwd={state['cwd']}",
        f"app_file={state['app_file']}",
        f"candidate_paths={state['candidate_paths']}",
        f"chosen_frontend_dist={state['chosen_frontend_dist']}",
        f"frontend_dist_exists={state['frontend_dist_exists']}",
        f"index_path={state['index_path']}",
        f"index_exists={state['index_exists']}",
        f"assets_path={state['assets_path']}",
        f"assets_exists={state['assets_exists']}",
        f"assets_files={state['assets_files']}",
        f"parent_listings={state['parent_listings']}",
        f"RAILWAY_ENVIRONMENT={state['env_railway']}",
        f"PORT={state['env_port']}",
        "=== end frontend runtime diagnostic ===",
    ]
    for line in lines:
        print(line, flush=True)
        logger.warning(line)
