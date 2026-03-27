"""Vote data models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.personas.models import Persona

class Vote(BaseModel):

    persona: Persona

    position: Literal["oui", "non", "abstention"]

    reasoning: str

class VoteTally(BaseModel):

    oui: int = 0

    non: int = 0

    abstention: int = 0

    oui_pct: float = 0.0

    non_pct: float = 0.0

    abstention_pct: float = 0.0

class VoteAnalysis(BaseModel):

    dominant_position: Literal["oui", "non", "abstention", "indecis"]

    margin: float = Field(ge=0.0, le=1.0)

    key_arguments: dict[str, list[str]]

    demographic_patterns: list[str]

    consensus_level: Literal["fort", "modere", "faible", "aucun"]

class SyntheticVoteResult(BaseModel):

    question: str

    population_profile: str

    total_voters: int

    votes: list[Vote]

    tally: VoteTally

    analysis: VoteAnalysis

    disclaimer: str
