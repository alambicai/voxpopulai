"""Vote API endpoints."""

from __future__ import annotations

import asyncio
import json
import logging
import threading

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.config import AppSettings
from app.events.event_log import generate_collaboration_id, reconstruct_session
from app.vote.orchestrator import (
    synthetic_population_vote,
    synthetic_vote_stream as vote_stream_fn,
)

logger = logging.getLogger(__name__)
router = APIRouter()

_running_votes: dict[str, dict] = {}
_running_votes_lock = threading.Lock()
class SyntheticVoteRequest(BaseModel):
    question: str
    population_profile: str
    num_voters: int = Field(default=20, ge=5, le=100)
    temperature: float = Field(default=0.8, ge=0.0, le=2.0)
    reuse_personas: bool = False
@router.post("/")
async def synthetic_vote(req: SyntheticVoteRequest) -> dict:
    """Vote synthetique par personas generes."""

    settings = AppSettings.load()
    persona_models = settings.synthetic.persona_models
    if not persona_models:
        raise HTTPException(
            status_code=400,
            detail="Aucun modele configure pour les personas. Allez dans Parametres > Vote synthetique.",
        )
    analysis_model = settings.synthetic.analysis_model
    generation_model = settings.synthetic.generation_model

    try:
        result = await synthetic_population_vote(
            question=req.question,
            population_profile=req.population_profile,
            num_voters=req.num_voters,
            persona_models=persona_models,
            analysis_model=analysis_model,
            generation_model=generation_model,
            temperature=req.temperature,
            reuse_personas=req.reuse_personas,
            generation_temperature=settings.synthetic.generation_temperature,
            judge_model=settings.synthetic.judge_model,
            judge_temperature=settings.synthetic.judge_temperature,
            judge_max_retries=settings.synthetic.judge_max_retries,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return result.model_dump()
@router.post("/stream")
def synthetic_vote_stream(req: SyntheticVoteRequest) -> StreamingResponse:
    """Vote synthetique avec streaming SSE de progression."""
    settings = AppSettings.load()
    persona_models = settings.synthetic.persona_models
    if not persona_models:
        raise HTTPException(
            status_code=400,
            detail="Aucun modele configure pour les personas. Allez dans Parametres > Vote synthetique.",
        )
    analysis_model = settings.synthetic.analysis_model
    generation_model = settings.synthetic.generation_model

    async def event_stream():
        try:
            async for event in vote_stream_fn(
                question=req.question,
                population_profile=req.population_profile,
                num_voters=req.num_voters,
                persona_models=persona_models,
                analysis_model=analysis_model,
                generation_model=generation_model,
                temperature=req.temperature,
                reuse_personas=req.reuse_personas,
                generation_temperature=settings.synthetic.generation_temperature,
                judge_model=settings.synthetic.judge_model,
                judge_temperature=settings.synthetic.judge_temperature,
                judge_max_retries=settings.synthetic.judge_max_retries,
            ):
                if event.get("phase") == "done":
                    yield f"data: {json.dumps({'type': 'done', 'result': event['result'].model_dump()})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'progress', **event})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
@router.post("/async")
async def synthetic_vote_async(req: SyntheticVoteRequest) -> dict:
    """Lance un vote synthetique en arriere-plan et retourne immediatement l'ID."""
    settings = AppSettings.load()
    persona_models = settings.synthetic.persona_models
    if not persona_models:
        raise HTTPException(
            status_code=400,
            detail="Aucun modele configure pour les personas. Allez dans Parametres > Vote synthetique.",
        )
    analysis_model = settings.synthetic.analysis_model
    generation_model = settings.synthetic.generation_model

    collab_id = generate_collaboration_id()

    with _running_votes_lock:
        _running_votes[collab_id] = {"status": "running"}

    async def _run_vote():
        try:
            await synthetic_population_vote(
                question=req.question,
                population_profile=req.population_profile,
                num_voters=req.num_voters,
                persona_models=persona_models,
                analysis_model=analysis_model,
                generation_model=generation_model,
                temperature=req.temperature,
                reuse_personas=req.reuse_personas,
                collaboration_id=collab_id,
                generation_temperature=settings.synthetic.generation_temperature,
                judge_model=settings.synthetic.judge_model,
                judge_temperature=settings.synthetic.judge_temperature,
                judge_max_retries=settings.synthetic.judge_max_retries,
            )
            with _running_votes_lock:
                _running_votes[collab_id] = {"status": "done"}
        except Exception as exc:
            logger.exception("Vote async %s echoue", collab_id)
            with _running_votes_lock:
                _running_votes[collab_id] = {"status": "error", "message": str(exc)}

    asyncio.create_task(_run_vote())

    return {"collaboration_id": collab_id, "status": "running"}
@router.get("/{collaboration_id}/status")
def synthetic_vote_status(collaboration_id: str) -> dict:
    """Retourne le statut d'un vote asynchrone."""
    with _running_votes_lock:
        tracked = _running_votes.get(collaboration_id)

    if tracked:
        return tracked

    session = reconstruct_session(collaboration_id)
    if session and session.get("result"):
        return {"status": "done"}

    raise HTTPException(status_code=404, detail="Vote introuvable.")
