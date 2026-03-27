"""Name generators for synthetic personas."""

from __future__ import annotations

import json

import logging

import random

from collections.abc import Callable

from pathlib import Path

logger = logging.getLogger(__name__)

NameGenerator = Callable[[dict[str, str]], str]

_REGISTRY: dict[str, NameGenerator] = {}

_DATA_DIR = Path(__file__).parent / "data"

def register_name_generator(name: str, fn: NameGenerator) -> None:

    _REGISTRY[name] = fn

def get_name_generator(name: str) -> NameGenerator:

    if name not in _REGISTRY:

        available = ", ".join(sorted(_REGISTRY))

        raise ValueError(f"Generator '{name}' unknown. Available: {available}")

    return _REGISTRY[name]

_PRENOMS: dict | None = None

_PATRONYMES: dict | None = None

def _load_json(filename: str) -> dict | list:

    with open(_DATA_DIR / filename, encoding="utf-8") as f:

        return json.load(f)

def _get_prenoms() -> dict:

    global _PRENOMS  # noqa: PLW0603

    if _PRENOMS is None:

        _PRENOMS = _load_json("prenoms_insee.json")

    return _PRENOMS

def _get_patronymes() -> dict:

    global _PATRONYMES  # noqa: PLW0603

    if _PATRONYMES is None:

        _PATRONYMES = _load_json("patronymes_france.json")

    return _PATRONYMES

_AGE_TO_DECADE: dict[str, str] = {

    "18-24 ans": "2000",

    "25-34 ans": "1990",

    "35-49 ans": "1980",

    "50-64 ans": "1970",

    "65+ ans": "1950",

}

_RELIGION_TO_CONTEXT: dict[str, str] = {

    "musulman": "musulman",

}

def _pick_weighted(pool: list[dict], key_name: str, key_weight: str) -> str:

    names = [p[key_name] for p in pool]

    weights = [p[key_weight] for p in pool]

    return random.choices(names, weights=weights, k=1)[0]  # nosec B311

def _insee_france_generator(attrs: dict[str, str]) -> str:

    prenoms_data = _get_prenoms()

    patronymes_data = _get_patronymes()

    sexe_key = "F" if attrs.get("sexe") == "femme" else "M"

    decade = _AGE_TO_DECADE.get(attrs.get("age", ""), "1980")

    context = _RELIGION_TO_CONTEXT.get(attrs.get("religion", ""), "default")

    decade_data = prenoms_data.get(sexe_key, {}).get(decade, {})

    pool = decade_data.get(context) or decade_data.get("default", [])

    if not pool:

        all_pools: list[dict] = []

        for d in prenoms_data.get(sexe_key, {}).values():

            all_pools.extend(d.get(context) or d.get("default", []))

        pool = all_pools or [{"prenom": "Jean" if sexe_key == "M" else "Marie", "poids": 1}]

    prenom = _pick_weighted(pool, "prenom", "poids")

    noms_pool = patronymes_data.get(context) or patronymes_data.get("default", [])

    nom = _pick_weighted(noms_pool, "nom", "poids")

    return f"{prenom} {nom}"

register_name_generator("insee_france", _insee_france_generator)
