"""Ollama models API endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger(__name__)
@router.get("/")
def list_models() -> list[dict]:
    """List available Ollama models."""

    try:
        import ollama as ollama_lib

        response = ollama_lib.list()
        models = response.get("models", []) if isinstance(response, dict) else []
        return [{"name": m.get("name", m.get("model", "")), "size": m.get("size", 0)} for m in models]
    except Exception:
        logger.warning("Failed to list Ollama models")
        return []
