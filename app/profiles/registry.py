"""Population profiles — definitions and loading.

Each profile defines demographic dimensions, their distribution weights,
and optionally descriptions to guide the LLM.

Profiles are loaded from JSON files in the definitions/ directory.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

_PROFILES_DIR = Path(__file__).parent / "definitions"

DimensionSpec = list[str] | dict[str, float | dict[str, Any]]


class PopulationProfile(BaseModel):
    """Population profile for synthetic persona generation."""

    model_config = ConfigDict(extra="ignore")

    name: str
    description: str
    icon: str = "🗳️"
    dimensions: dict[str, DimensionSpec]
    context: str = ""
    sources: list[str] = Field(default_factory=list)
    name_generator: dict | None = None

    def get_values(self, dimension: str) -> list[str]:
        """Return value names for a dimension."""
        entries = self.dimensions[dimension]
        if isinstance(entries, list):
            return list(entries)
        return list(entries.keys())

    def get_all_values(self) -> dict[str, list[str]]:
        """Return dict[dimension, list[value]]."""
        return {dim: self.get_values(dim) for dim in self.dimensions}

    def _raw_weight(self, dimension: str, value: str) -> float | None:
        """Raw weight before normalization."""
        entries = self.dimensions[dimension]
        if isinstance(entries, list):
            return None
        entry = entries[value]
        if isinstance(entry, int | float):
            return float(entry)
        if isinstance(entry, dict):
            w = entry.get("weight")
            return float(w) if w is not None else None
        return None

    def get_weights(self, dimension: str) -> dict[str, float]:
        """Return {value: weight} normalized (sum = 1.0)."""
        values = self.get_values(dimension)
        n = len(values)
        raw = {v: self._raw_weight(dimension, v) for v in values}

        if all(w is None for w in raw.values()):
            return {v: 1.0 / n for v in values}

        weights = {v: (w if w is not None else 0.0) for v, w in raw.items()}
        total = sum(weights.values())

        if total > 0 and abs(total - 1.0) > 1e-6:
            return {v: w / total for v, w in weights.items()}
        if total == 0:
            return {v: 1.0 / n for v in values}
        return weights

    def get_weight(self, dimension: str, value: str) -> float:
        """Return the normalized weight of a value."""
        return self.get_weights(dimension)[value]

    def get_description(self, dimension: str, value: str) -> str:
        """Return description for a value, or empty string."""
        entries = self.dimensions[dimension]
        if isinstance(entries, list):
            return ""
        entry = entries.get(value)
        if isinstance(entry, dict):
            return entry.get("description", "")
        return ""

    def get_descriptions(self, dimension: str) -> dict[str, str]:
        """Return {value: description} for a dimension."""
        return {v: self.get_description(dimension, v) for v in self.get_values(dimension)}


def _load_profiles() -> dict[str, PopulationProfile]:
    """Load all JSON profiles from definitions/ directory."""
    profiles: dict[str, PopulationProfile] = {}
    if not _PROFILES_DIR.exists():
        return profiles
    for path in sorted(_PROFILES_DIR.glob("*.json")):
        with open(path) as f:
            data = json.load(f)
        profile = PopulationProfile(**data)
        if profile.name in profiles:
            raise ValueError(f"Duplicate profile: '{profile.name}' defined multiple times.")
        profiles[profile.name] = profile
    return profiles


_PROFILES: dict[str, PopulationProfile] = _load_profiles()


def register_profile(profile: PopulationProfile) -> None:
    """Register an additional profile."""
    if profile.name in _PROFILES:
        raise ValueError(f"Profile '{profile.name}' already registered.")
    _PROFILES[profile.name] = profile


def get_profile(name: str) -> PopulationProfile:
    """Return a profile by name."""
    profile = _PROFILES.get(name)
    if not profile:
        available = ", ".join(sorted(_PROFILES.keys()))
        raise ValueError(f"Profile '{name}' not found. Available: {available}")
    return profile


def list_profiles() -> list[PopulationProfile]:
    """Return all available profiles sorted by name."""
    return sorted(_PROFILES.values(), key=lambda p: p.name)


def get_distribution_weights(profile: PopulationProfile) -> dict[str, dict[str, float]]:
    """Calculate distribution weights for a profile."""
    return {dim: profile.get_weights(dim) for dim in profile.dimensions}


def load_sources_content(profile: PopulationProfile) -> str:
    """Load and concatenate source file contents for a profile."""
    if not profile.sources:
        return ""

    parts: list[str] = []
    for source_path in profile.sources:
        full_path = _PROFILES_DIR / source_path
        if not full_path.is_file():
            logger.warning("Source not found for profile '%s': %s", profile.name, source_path)
            continue
        try:
            content = full_path.read_text(encoding="utf-8")
            if content.strip():
                parts.append(content.strip())
        except Exception:
            logger.exception(
                "Error reading source '%s' for profile '%s'", source_path, profile.name
            )

    return "\n\n---\n\n".join(parts)
