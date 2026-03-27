"""Settings API endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.config import AppSettings
from app.llm.queue import get_queue

router = APIRouter()
@router.get("/")
def get_settings() -> dict:
    """Load current settings."""

    settings = AppSettings.load()
    return settings.model_dump(mode="json")
@router.put("/synthetic")
def update_synthetic_settings(data: dict) -> dict:
    """Update synthetic vote settings (partial update)."""
    settings = AppSettings.load()
    current = settings.synthetic.model_dump()
    current.update(data)
    settings.synthetic = type(settings.synthetic)(**current)
    settings.save()
    return settings.synthetic.model_dump(mode="json")
@router.put("/ollama")
def update_ollama_settings(data: dict) -> dict:
    """Update Ollama runtime settings (partial update)."""
    settings = AppSettings.load()
    current = settings.ollama.model_dump()
    current.update(data)
    settings.ollama = type(settings.ollama)(**current)
    settings.save()
    # Update the running queue's settings
    queue = get_queue()
    queue.ollama_settings = settings.ollama
    return settings.ollama.model_dump(mode="json")
