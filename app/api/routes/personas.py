"""Personas API endpoints."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.config import AppSettings
from app.personas.store import PersonaStore

logger = logging.getLogger(__name__)
router = APIRouter()
@router.get("/stats")
def personas_stats() -> dict:
    """Global persona statistics."""

    store = PersonaStore()
    return store.count_all()
@router.get("/distribution/{profile_name}")
def personas_distribution(profile_name: str) -> dict:
    """Attribute distribution + theoretical weights for a profile."""
    from app.profiles.registry import get_distribution_weights, get_profile

    store = PersonaStore()
    actual = store.get_attribute_distribution(profile_name)
    try:
        profile = get_profile(profile_name)
        theoretical = get_distribution_weights(profile)
    except ValueError:
        theoretical = {}
    return {
        "actual": actual,
        "theoretical": theoretical,
        "total": store.count_by_profile(profile_name),
    }
@router.get("/")
def list_personas(profile: str | None = None, offset: int = 0, limit: int = 50) -> dict:
    """Paginated persona listing."""
    store = PersonaStore()
    rows, total = store.list_paginated(profile, offset, limit)
    return {"personas": rows, "total": total, "offset": offset, "limit": limit}
class GeneratePersonasRequest(BaseModel):
    profile_name: str
    count: int = Field(default=20, ge=1, le=100)
@router.post("/generate")
async def generate_personas_endpoint(req: GeneratePersonasRequest) -> dict:
    """Generate personas and persist them."""
    from app.personas.generator import generate_personas
    from app.profiles.registry import get_profile

    settings = AppSettings.load()
    generation_model = settings.synthetic.generation_model
    persona_models = settings.synthetic.persona_models

    try:
        profile = get_profile(req.profile_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    personas = await generate_personas(
        profile,
        req.count,
        generation_model,
        assigned_models=persona_models or None,
        temperature=settings.synthetic.generation_temperature,
        judge_model=settings.synthetic.judge_model,
        judge_temperature=settings.synthetic.judge_temperature,
        judge_max_retries=settings.synthetic.judge_max_retries,
    )
    store = PersonaStore()
    store.save_batch_multi(personas, req.profile_name)
    return {"generated": len(personas), "profile": req.profile_name, "model": generation_model}
@router.post("/generate/stream")
def generate_personas_stream(req: GeneratePersonasRequest) -> StreamingResponse:
    """Generate personas with SSE progress streaming."""
    from app.personas.generator import generate_personas_iter
    from app.profiles.registry import get_profile

    settings = AppSettings.load()
    generation_model = settings.synthetic.generation_model
    persona_models = settings.synthetic.persona_models

    try:
        profile = get_profile(req.profile_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    async def event_stream():
        store = PersonaStore()
        generated = 0
        try:
            async for current, total, persona in generate_personas_iter(
                profile,
                req.count,
                generation_model,
                assigned_models=persona_models or None,
                temperature=settings.synthetic.generation_temperature,
                judge_model=settings.synthetic.judge_model,
                judge_temperature=settings.synthetic.judge_temperature,
                judge_max_retries=settings.synthetic.judge_max_retries,
            ):
                store.save(persona, req.profile_name, persona.model)
                generated += 1
                yield f"data: {json.dumps({'type': 'progress', 'current': current, 'total': total, 'persona_name': persona.name})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'generated': generated, 'profile': req.profile_name, 'model': generation_model})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
@router.get("/{profile_name}/models")
def personas_models(profile_name: str) -> dict:
    """List models used for a profile."""
    store = PersonaStore()
    return {"models": store.models_for_profile(profile_name)}
@router.delete("/{profile_name}/attribute")
def delete_personas_by_attribute(profile_name: str, dimension: str, value: str) -> dict:
    """Delete personas with a specific attribute value."""
    store = PersonaStore()
    count = store.delete_by_attribute(profile_name, dimension, value)
    return {"deleted": count}
@router.delete("/{profile_name}/model/{model_name}")
def delete_personas_by_model(profile_name: str, model_name: str) -> dict:
    """Delete personas by generation model."""
    store = PersonaStore()
    count = store.delete_by_profile_and_model(profile_name, model_name)
    return {"deleted": count}
@router.delete("/{profile_name}")
def delete_personas_by_profile(profile_name: str) -> dict:
    """Delete all personas for a profile."""
    store = PersonaStore()
    count = store.delete_by_profile(profile_name)
    return {"deleted": count}
