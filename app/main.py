"""VoxPopulAI — synthetic population voting simulator."""

from __future__ import annotations

import contextlib
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.llm.queue import get_queue

logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).parent / "frontend"


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Start/stop the OllamaQueue worker."""
    queue = get_queue()
    await queue.start()
    logger.info("VoxPopulAI started")
    yield
    await queue.stop()
    logger.info("VoxPopulAI stopped")


app = FastAPI(
    title="VoxPopulAI",
    description="Synthetic population voting simulator powered by LLMs",
    version="0.1.0",
    lifespan=lifespan,
)

# --- API routes ---

from app.api.routes.history import router as history_router
from app.api.routes.models import router as models_router
from app.api.routes.personas import router as personas_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.settings import router as settings_router
from app.api.routes.vote import router as vote_router

app.include_router(vote_router, prefix="/api/vote", tags=["vote"])
app.include_router(profiles_router, prefix="/api/profiles", tags=["profiles"])
app.include_router(personas_router, prefix="/api/personas", tags=["personas"])
app.include_router(history_router, prefix="/api/history", tags=["history"])
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])
app.include_router(models_router, prefix="/api/models", tags=["models"])

# --- Static files ---

app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")


@app.get("/")
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")


# --- Logging ---

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
