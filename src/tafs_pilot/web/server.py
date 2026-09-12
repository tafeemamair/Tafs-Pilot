"""Web production console server for Taf's Pilot.

Serves the desktop-first production console, API endpoints, and artifacts
with HTTP Range request streaming support for video preview.
"""

import argparse
import json
import os
import sys
import webbrowser
from pathlib import Path
from typing import Any, Dict

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
import uvicorn

# Root directory of the repository
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"
ARTIFACTS_DIR = BASE_DIR / "artifacts"


def get_default_brief() -> Dict[str, Any]:
    """Returns the default hackathon demo brief."""
    return {
        "topic": "Why Senior Engineers Write Less Code Than Juniors",
        "audience": "Software engineers, tech leads, and developers",
        "goal": "Create a high-impact short-form video demonstrating that senior engineering value comes from simplicity, deletion, and preventing outages rather than raw output.",
        "tone": "Direct, authoritative, punchy, insightful",
        "duration": "20–30 seconds",
        "approximate_duration": 21,
        "platform": "YouTube Shorts / TikTok / Instagram Reels",
    }


async def health_check(request: Request) -> JSONResponse:
    """Returns agent readiness and system health."""
    return JSONResponse(
        {
            "status": "ready",
            "agent_name": "Taf's Pilot",
            "subtitle": "Autonomous Video Production Agent",
            "assistant_status": "Production Assistant • Ready",
            "active_project_id": "74ed7661",
        }
    )


async def get_brief(request: Request) -> JSONResponse:
    """Returns the default demo brief values."""
    return JSONResponse(get_default_brief())


async def get_project_data(request: Request) -> JSONResponse:
    """Loads project artifact metadata for the given project ID (default 74ed7661)."""
    project_id = request.path_params.get("project_id", "74ed7661")
    project_dir = ARTIFACTS_DIR / project_id

    final_video = project_dir / "final.mp4"
    defect_video = project_dir / "final_defect.mp4"
    qc_file = project_dir / "qc.json"
    audit_file = project_dir / "audit_history.json"
    revision_file = project_dir / "revision_decision.json"

    qc_data = {}
    if qc_file.exists():
        try:
            with open(qc_file, "r", encoding="utf-8") as f:
                qc_data = json.load(f)
        except Exception:
            pass

    audit_history = []
    if audit_file.exists():
        try:
            with open(audit_file, "r", encoding="utf-8") as f:
                audit_history = json.load(f)
        except Exception:
            pass

    revision_decision = {}
    if revision_file.exists():
        try:
            with open(revision_file, "r", encoding="utf-8") as f:
                revision_decision = json.load(f)
        except Exception:
            pass

    final_video_url = f"/artifacts/{project_id}/final.mp4" if final_video.exists() else None
    defect_video_url = f"/artifacts/{project_id}/final_defect.mp4" if defect_video.exists() else None

    return JSONResponse(
        {
            "project_id": project_id,
            "brief": get_default_brief(),
            "final_video_url": final_video_url,
            "defect_video_url": defect_video_url,
            "qc": qc_data,
            "audit_history": audit_history,
            "revision_decision": revision_decision,
            "hooks": [
                {
                    "id": "hook-1",
                    "number": "01",
                    "text": "The best senior engineers don't write more code. They delete it.",
                    "recommended": True,
                    "angle": "Counterintuitive senior engineering philosophy",
                },
                {
                    "id": "hook-2",
                    "number": "02",
                    "text": "Juniors count lines committed. Seniors count problems prevented.",
                    "recommended": False,
                    "angle": "Direct metric contrast: activity vs impact",
                },
                {
                    "id": "hook-3",
                    "number": "03",
                    "text": "The fastest code in production is the code you never wrote.",
                    "recommended": False,
                    "angle": "Architectural simplicity and performance",
                },
            ],
            "scenes": [
                {
                    "scene_id": 1,
                    "type": "MG",
                    "visual": "Terminal git diff showing 450 lines of legacy bloat deleted, with bold hero punch: 'THEY DELETE IT.'",
                    "narration": "The best senior engineers don't write more code. They delete it.",
                    "duration": 5.1,
                },
                {
                    "scene_id": 2,
                    "type": "DEMO",
                    "visual": "High-contrast comparison cards: Junior Metric (+2,480 Lines Committed) vs Senior Metric (Problems Prevented: 100%).",
                    "narration": "Juniors measure their value in lines of code committed. Seniors measure their value in problems prevented and systems simplified.",
                    "duration": 8.6,
                },
                {
                    "scene_id": 3,
                    "type": "MG",
                    "visual": "Terminal command execution 'tafs-pilot --simplify-architecture' with hero callout 'WHAT CAN I SIMPLIFY TODAY?'",
                    "narration": "Before you write another line of code today, ask yourself: What can I simplify or delete right now?",
                    "duration": 7.0,
                },
            ],
        }
    )


async def serve_index(request: Request) -> FileResponse:
    """Serves the main web console HTML page."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return Response("index.html not found", status_code=404)
    return FileResponse(str(index_path))


def create_app() -> Starlette:
    """Builds and configures the Starlette application."""
    routes = [
        Route("/", endpoint=serve_index),
        Route("/index.html", endpoint=serve_index),
        Route("/api/health", endpoint=health_check),
        Route("/api/brief/default", endpoint=get_brief),
        Route("/api/project/{project_id}", endpoint=get_project_data),
    ]

    # Ensure static and artifact directories exist
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # Mount static assets
    routes.append(Mount("/static", app=StaticFiles(directory=str(STATIC_DIR)), name="static"))
    # Mount artifacts for direct media playback
    routes.append(Mount("/artifacts", app=StaticFiles(directory=str(ARTIFACTS_DIR)), name="artifacts"))

    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]

    return Starlette(debug=True, routes=routes, middleware=middleware)


app = create_app()


def run_server(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = False):
    """Starts the Uvicorn web server."""
    url = f"http://{host}:{port}"
    print("\n" + "=" * 68)
    print("  TAF'S PILOT - Production Console")
    print(f"  Console URL: {url}")
    print("  Autonomous Video Production Agent | Hackathon Demo")
    print("=" * 68 + "\n")

    if open_browser:
        webbrowser.open(url)

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Taf's Pilot Web Production Console")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host IP")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--open", action="store_true", help="Automatically open browser")
    args = parser.parse_args()

    run_server(host=args.host, port=args.port, open_browser=args.open)
