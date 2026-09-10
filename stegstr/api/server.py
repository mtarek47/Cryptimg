"""
FastAPI Server & Web UI Mount
"""

import asyncio
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from stegstr.api.routes import router as api_router
from stegstr.storage.db import DatabaseManager
from stegstr.config import API_HOST, API_PORT

app = FastAPI(
    title="Crypt API",
    description="Crypt Steganographic Social Networking REST API & OpenAPI Engine",
    version="1.0.0"
)

app.include_router(api_router)

# Mount static web UI directory
UI_DIR = Path(__file__).resolve().parent.parent / "ui" / "static"
UI_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")

db = DatabaseManager()


async def periodic_24h_cleanup():
    while True:
        try:
            db.cleanup_expired_events(86400)
        except Exception:
            pass
        await asyncio.sleep(1800)  # Check every 30 minutes


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(periodic_24h_cleanup())


@app.get("/app", response_class=FileResponse)
def serve_ui():
    index_file = UI_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Crypt Web UI under construction"}


@app.get("/")
def read_root():
    return {
        "app": "Crypt Engine",
        "documentation": "/docs",
        "web_ui": "/app",
        "status": "ONLINE"
    }


def start_server(host: str = API_HOST, port: int = API_PORT):
    import uvicorn
    uvicorn.run("stegstr.api.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    start_server()
