"""Population profiles API endpoints."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_population_profiles() -> dict:
    """List all available population profiles."""

    from app.profiles.registry import list_profiles

    profiles = list_profiles()
    return {
        "profiles": [
            {
                "name": p.name,
                "description": p.description,
                "icon": p.icon,
                "dimensions": p.get_all_values(),
                "context": p.context,
                "sources": p.sources,
            }
            for p in profiles
        ]
    }
