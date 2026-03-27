"""PersonaStore — SQLite persistence for generated personas."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone

from app.personas.models import Persona

_DEFAULT_DB_PATH = "./data/personas.db"
class PersonaStore:
    """SQLite storage for generated personas."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.environ.get("PERSONA_DB_PATH", _DEFAULT_DB_PATH)
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self._ensure_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS personas (
                    id TEXT PRIMARY KEY,
                    profile_name TEXT NOT NULL,
                    name TEXT NOT NULL,
                    attributes TEXT NOT NULL,
                    system_prompt TEXT NOT NULL,
                    background TEXT NOT NULL,
                    model TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_personas_profile
                ON personas (profile_name)
                """
            )

    def save(self, persona: Persona, profile_name: str, model: str) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO personas (id, profile_name, name, attributes,
                                      system_prompt, background, model, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    persona.id,
                    profile_name,
                    persona.name,
                    json.dumps(persona.attributes, ensure_ascii=False),
                    persona.system_prompt,
                    persona.background,
                    model,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def save_batch(self, personas: list[Persona], profile_name: str, model: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.executemany(
                """
                INSERT INTO personas (id, profile_name, name, attributes,
                                      system_prompt, background, model, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        p.id, profile_name, p.name,
                        json.dumps(p.attributes, ensure_ascii=False),
                        p.system_prompt, p.background, model, now,
                    )
                    for p in personas
                ],
            )

    def save_batch_multi(self, personas: list[Persona], profile_name: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.executemany(
                """
                INSERT INTO personas (id, profile_name, name, attributes,
                                      system_prompt, background, model, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        p.id, profile_name, p.name,
                        json.dumps(p.attributes, ensure_ascii=False),
                        p.system_prompt, p.background, p.model, now,
                    )
                    for p in personas
                ],
            )

    def get(self, persona_id: str) -> Persona | None:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM personas WHERE id = ?", (persona_id,)).fetchone()
        if not row:
            return None
        return _row_to_persona(row)

    def list_by_profile(self, profile_name: str) -> list[Persona]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM personas WHERE profile_name = ? ORDER BY created_at",
                (profile_name,),
            ).fetchall()
        return [_row_to_persona(r) for r in rows]

    def count_by_profile(self, profile_name: str) -> int:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM personas WHERE profile_name = ?",
                (profile_name,),
            ).fetchone()
        return row["cnt"]

    def sample(self, profile_name: str, count: int) -> list[Persona]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM personas WHERE profile_name = ? ORDER BY RANDOM() LIMIT ?",
                (profile_name, count),
            ).fetchall()
        return [_row_to_persona(r) for r in rows]

    def delete_by_profile(self, profile_name: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM personas WHERE profile_name = ?", (profile_name,))
        return cursor.rowcount

    def delete_by_profile_and_model(self, profile_name: str, model: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM personas WHERE profile_name = ? AND model = ?",
                (profile_name, model),
            )
        return cursor.rowcount

    def models_for_profile(self, profile_name: str) -> list[str]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT model FROM personas WHERE profile_name = ? ORDER BY model",
                (profile_name,),
            ).fetchall()
        return [r["model"] for r in rows]

    def count_all(self) -> dict:
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) as cnt FROM personas").fetchone()["cnt"]
            profile_rows = conn.execute(
                "SELECT profile_name, COUNT(*) as cnt FROM personas GROUP BY profile_name ORDER BY cnt DESC"
            ).fetchall()
            model_rows = conn.execute(
                "SELECT model, COUNT(*) as cnt FROM personas GROUP BY model ORDER BY cnt DESC"
            ).fetchall()
        return {
            "total": total,
            "by_profile": {r["profile_name"]: r["cnt"] for r in profile_rows},
            "by_model": {r["model"]: r["cnt"] for r in model_rows},
        }

    def get_attribute_distribution(self, profile_name: str) -> dict[str, dict[str, int]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT attributes FROM personas WHERE profile_name = ?",
                (profile_name,),
            ).fetchall()
        dist: dict[str, dict[str, int]] = {}
        for row in rows:
            attrs = json.loads(row["attributes"])
            for dim, val in attrs.items():
                if dim not in dist:
                    dist[dim] = {}
                dist[dim][val] = dist[dim].get(val, 0) + 1
        return dist

    def delete_by_attribute(self, profile_name: str, dimension: str, value: str) -> int:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT id, attributes FROM personas WHERE profile_name = ?",
                (profile_name,),
            ).fetchall()
            ids_to_delete = []
            for row in rows:
                attrs = json.loads(row["attributes"])
                if attrs.get(dimension) == value:
                    ids_to_delete.append(row["id"])
            if not ids_to_delete:
                return 0
            placeholders = ",".join("?" for _ in ids_to_delete)
            cursor = conn.execute(
                f"DELETE FROM personas WHERE id IN ({placeholders})",  # noqa: S608
                ids_to_delete,
            )
        return cursor.rowcount

    def list_paginated(
        self, profile_name: str | None, offset: int, limit: int
    ) -> tuple[list[dict], int]:
        with self._get_connection() as conn:
            if profile_name:
                total = conn.execute(
                    "SELECT COUNT(*) as cnt FROM personas WHERE profile_name = ?",
                    (profile_name,),
                ).fetchone()["cnt"]
                rows = conn.execute(
                    "SELECT * FROM personas WHERE profile_name = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (profile_name, limit, offset),
                ).fetchall()
            else:
                total = conn.execute("SELECT COUNT(*) as cnt FROM personas").fetchone()["cnt"]
                rows = conn.execute(
                    "SELECT * FROM personas ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                ).fetchall()
        return (
            [
                {
                    "id": r["id"],
                    "profile_name": r["profile_name"],
                    "name": r["name"],
                    "attributes": json.loads(r["attributes"]),
                    "model": r["model"],
                    "created_at": r["created_at"],
                    "background": r["background"],
                    "system_prompt": r["system_prompt"],
                }
                for r in rows
            ],
            total,
        )
def _row_to_persona(row: sqlite3.Row) -> Persona:
    """Convert a SQLite row to Persona."""
    return Persona(
        id=row["id"],
        name=row["name"],
        attributes=json.loads(row["attributes"]),
        system_prompt=row["system_prompt"],
        background=row["background"],
        model=row["model"],
    )
