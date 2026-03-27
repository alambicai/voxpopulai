"""Persona data model."""

from __future__ import annotations

from pydantic import BaseModel
class Persona(BaseModel):
    """Synthetic persona generated from a population profile."""

    id: str
    name: str
    attributes: dict[str, str]
    system_prompt: str
    background: str
    model: str = ""
