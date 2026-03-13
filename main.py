"""
BTU Virtual University – Application Entry Point
Run with:  python main.py
"""

import os
import sys
import threading
import webbrowser
import uvicorn

# Fix Windows console encoding for Unicode output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Make sure the project root is on sys.path ─────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from api.app import app  # noqa: E402 – import after path fix


def main() -> None:
    host    = os.getenv("HOST",       "0.0.0.0")
    port    = int(os.getenv("PORT",   "8080"))
    reload  = os.getenv("APP_ENV",    "development") == "development"
    workers = int(os.getenv("WORKERS", "1"))
    log_lvl = os.getenv("LOG_LEVEL",  "info").lower()

    print(
        f"\n"
        f"  ╔══════════════════════════════════════════════════╗\n"
        f"  ║   BTU Virtual University – Multi-Agentic AI      ║\n"
        f"  ║   http://{host}:{port}                              ║\n"
        f"  ║   Docs: http://{host}:{port}/docs                   ║\n"
        f"  ╚══════════════════════════════════════════════════╝\n"
    )

    # Auto-open browser after a short delay (gives uvicorn time to boot)
    url = f"http://localhost:{port}"
    threading.Timer(2.0, lambda: webbrowser.open(url)).start()

    uvicorn.run(
        "api.app:app",
        host=host,
        port=port,
        reload=reload,
        workers=1 if reload else workers,   # reload mode requires 1 worker
        log_level=log_lvl,
    )


if __name__ == "__main__":
    main()
