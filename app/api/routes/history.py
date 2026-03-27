"""History API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.events.event_log import (
    audit_vote_session,
    list_sessions,
    reconstruct_session,
)

router = APIRouter()
@router.get("/")
def collaboration_history(
    mode: str | None = None,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Paginated session history."""

    sessions, total = list_sessions(mode=mode, search=search, limit=limit, offset=offset)
    return {"sessions": sessions, "total": total, "offset": offset, "limit": limit}
@router.get("/{collaboration_id}")
def collaboration_session(collaboration_id: str) -> dict:
    """Reconstruct a session from the Event Log."""
    result = reconstruct_session(collaboration_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session introuvable.")
    return result
@router.get("/{collaboration_id}/audit")
def collaboration_vote_audit(collaboration_id: str) -> dict:
    """Cross-tab audit: vote x persona attributes."""
    result = audit_vote_session(collaboration_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Session introuvable ou n'est pas un vote synthetique.",
        )
    return result
