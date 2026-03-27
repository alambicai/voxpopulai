"""Event Log — persistance des evenements de vote synthetique.

Table SQLite events dans data/events.db.
Permet l'historique et l'analyse cross-sessions.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone

DATA_DIR = os.environ.get("DATA_DIR", "./data")
DB_PATH = os.path.join(DATA_DIR, "events.db")

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS events (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp         TEXT    NOT NULL,
    type              TEXT    NOT NULL,
    collaboration_id  TEXT,
    workspace         TEXT,
    agent             TEXT,
    model             TEXT,
    data              TEXT    NOT NULL
);
"""

_CREATE_INDICES = [
    "CREATE INDEX IF NOT EXISTS idx_events_collab_id ON events (collaboration_id);",
    "CREATE INDEX IF NOT EXISTS idx_events_type_ts ON events (type, timestamp);",
]
def _get_connection() -> sqlite3.Connection:
    """Ouvre une connexion SQLite et cree la table si besoin."""
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(_CREATE_TABLE)
    for idx in _CREATE_INDICES:
        conn.execute(idx)
    conn.commit()
    return conn
def generate_collaboration_id() -> str:
    """Genere un ID unique pour une session de collaboration."""
    return uuid.uuid4().hex[:12]
def emit_event(
    type: str,
    collaboration_id: str | None = None,
    workspace: str | None = None,
    agent: str | None = None,
    model: str | None = None,
    data: dict | None = None,
) -> int:
    """Enregistre un evenement dans l'Event Log.

    Returns:
        ID de l'evenement insere.
    """
    ts = datetime.now(timezone.utc).isoformat()
    data_json = json.dumps(data or {}, ensure_ascii=False)

    conn = _get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO events (timestamp, type, collaboration_id, workspace, agent, model, data)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ts, type, collaboration_id, workspace, agent, model, data_json),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
def list_sessions(
    mode: str | None = None,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Liste les sessions de vote passees.

    Returns:
        (sessions, total_count)
    """
    conn = _get_connection()
    try:
        count_sql = "SELECT COUNT(*) FROM events WHERE type = 'collaboration_start'"
        count_params: list = []

        if mode:
            count_sql += " AND json_extract(data, '$.mode') = ?"
            count_params.append(mode)
        if search:
            count_sql += " AND json_extract(data, '$.topic') LIKE ?"
            count_params.append(f"%{search}%")

        total = conn.execute(count_sql, count_params).fetchone()[0]

        query = (
            "SELECT collaboration_id, timestamp, data FROM events"
            " WHERE type = 'collaboration_start'"
        )
        params: list = []

        if mode:
            query += " AND json_extract(data, '$.mode') = ?"
            params.append(mode)
        if search:
            query += " AND json_extract(data, '$.topic') LIKE ?"
            params.append(f"%{search}%")

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        sessions = []
        for collab_id, ts, data_json in rows:
            start_data = json.loads(data_json)

            end_row = conn.execute(
                "SELECT data FROM events"
                " WHERE collaboration_id = ? AND type = 'collaboration_end'"
                " LIMIT 1",
                (collab_id,),
            ).fetchone()
            end_data = json.loads(end_row[0]) if end_row else {}

            sessions.append(
                {
                    "collaboration_id": collab_id,
                    "timestamp": ts,
                    "mode": start_data.get("mode", "unknown"),
                    "topic": start_data.get("topic", ""),
                    "agents": start_data.get("agents", []),
                    **{k: v for k, v in end_data.items() if k != "mode"},
                }
            )

        return sessions, total
    finally:
        conn.close()
def get_session_events(collaboration_id: str) -> list[dict]:
    """Recupere tous les evenements d'une session.

    Returns:
        Liste ordonnee par timestamp.
    """
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT id, timestamp, type, agent, model, data FROM events"
            " WHERE collaboration_id = ? ORDER BY id",
            (collaboration_id,),
        ).fetchall()
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "type": row[2],
                "agent": row[3],
                "model": row[4],
                "data": json.loads(row[5]),
            }
            for row in rows
        ]
    finally:
        conn.close()
def reconstruct_session(collaboration_id: str) -> dict:
    """Reconstruit le resultat complet d'une session depuis les evenements.

    Returns:
        {mode: str, result: dict}
    """
    events = get_session_events(collaboration_id)
    if not events:
        return {}

    start_event = next((e for e in events if e["type"] == "collaboration_start"), None)
    end_event = next((e for e in events if e["type"] == "collaboration_end"), None)

    if not start_event:
        return {}

    mode = start_event["data"].get("mode", "unknown")

    if mode == "synthetic_vote":
        return _reconstruct_vote(events, start_event, end_event)
    return {}
_POSITION_MIGRATION = {"pour": "oui", "contre": "non", "neutre": "abstention"}
def _migrate_vote_result(result: dict) -> dict:
    """Migre les anciens resultats pour/contre/neutre vers oui/non/abstention."""
    if not result:
        return result

    tally = result.get("tally", {})
    if "pour" not in tally:
        return result

    result["tally"] = {
        "oui": tally.get("pour", 0),
        "non": tally.get("contre", 0),
        "abstention": tally.get("neutre", 0),
        "oui_pct": tally.get("pour_pct", 0.0),
        "non_pct": tally.get("contre_pct", 0.0),
        "abstention_pct": tally.get("neutre_pct", 0.0),
    }

    for vote in result.get("votes", []):
        old_pos = vote.get("position", "")
        if old_pos in _POSITION_MIGRATION:
            vote["position"] = _POSITION_MIGRATION[old_pos]

    analysis = result.get("analysis", {})
    if analysis:
        dom = analysis.get("dominant_position", "")
        if dom in _POSITION_MIGRATION:
            analysis["dominant_position"] = _POSITION_MIGRATION[dom]

        key_args = analysis.get("key_arguments", {})
        new_key_args = {}
        for old_key, new_key in [("pour", "oui"), ("contre", "non")]:
            if old_key in key_args:
                new_key_args[new_key] = key_args[old_key]
        for k, v in key_args.items():
            if k not in ("pour", "contre"):
                new_key_args[k] = v
        if new_key_args:
            analysis["key_arguments"] = new_key_args

    return result
def _reconstruct_vote(events, start_event, end_event) -> dict:
    """Reconstruit une session vote synthetique."""
    if end_event and "result" in end_event["data"]:
        result = end_event["data"]["result"]
        return {"mode": "synthetic_vote", "result": _migrate_vote_result(result)}
    return {"mode": "synthetic_vote", "result": {}}
def audit_vote_session(collaboration_id: str) -> dict | None:
    """Produit un audit croise vote x persona pour une session de vote synthetique.

    Returns:
        None si la session n'existe pas ou n'est pas un vote synthetique.
        Sinon un dict {question, profile, total, votes, cross_tabs}.
    """
    session = reconstruct_session(collaboration_id)
    if not session or session.get("mode") != "synthetic_vote":
        return None

    result = session.get("result", {})
    if not result:
        return None

    raw_votes = result.get("votes", [])
    if not raw_votes:
        return None

    votes_audit: list[dict] = []
    for v in raw_votes:
        persona = v.get("persona", {})
        votes_audit.append(
            {
                "persona_id": persona.get("id", ""),
                "persona_name": persona.get("name", ""),
                "attributes": persona.get("attributes", {}),
                "model": persona.get("model", ""),
                "position": v.get("position", ""),
                "reasoning": v.get("reasoning", ""),
                "system_prompt": persona.get("system_prompt", ""),
            }
        )

    dimensions: set[str] = set()
    for va in votes_audit:
        dimensions.update(va["attributes"].keys())

    cross_tabs: dict[str, dict[str, dict[str, int]]] = {}
    for dim in sorted(dimensions):
        cross_tabs[dim] = {}
        for va in votes_audit:
            val = va["attributes"].get(dim, "")
            if val not in cross_tabs[dim]:
                cross_tabs[dim][val] = {"oui": 0, "non": 0, "abstention": 0, "total": 0}
            cross_tabs[dim][val][va["position"]] += 1
            cross_tabs[dim][val]["total"] += 1

    cross_tabs["_model"] = {}
    for va in votes_audit:
        model = va["model"]
        if model not in cross_tabs["_model"]:
            cross_tabs["_model"][model] = {"oui": 0, "non": 0, "abstention": 0, "total": 0}
        cross_tabs["_model"][model][va["position"]] += 1
        cross_tabs["_model"][model]["total"] += 1

    return {
        "question": result.get("question", ""),
        "population_profile": result.get("population_profile", ""),
        "total_voters": len(votes_audit),
        "tally": result.get("tally", {}),
        "votes": votes_audit,
        "cross_tabs": cross_tabs,
    }
