# VoxPopulAI - Architecture

## Vue d'ensemble

```text
┌─────────────────────────────────────────────────────────────────┐
│                       INTERFACES                                │
│                                                                 │
│   SPA vanilla JS (servi par FastAPI)                            │
│   ├── Vote (création, streaming, résultats)                     │
│   ├── Personas (génération, stats, distributions)               │
│   ├── History (sessions passées, audit)                         │
│   └── Settings (modèles LLM, paramètres)                          │
│                                                                 │
│   FastAPI backend (:8000)                                       │
│   ├── REST : /api/vote/ (sync + SSE stream + async)             │
│   ├── REST : /api/personas/ (CRUD + génération SSE)             │
│   ├── REST : /api/profiles/ (liste profils)                     │
│   ├── REST : /api/history/ (sessions + audit)                   │
│   ├── REST : /api/settings/ (configuration)                     │
│   └── Static files (sert la SPA)                                │
│                                                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                    SERVICES LAYER                                │
│                          │                                       │
│   ┌──────────────────────┴───────────────────────┐                 │
│   │              Voting System                  │                 │
│   │  • vote/orchestrator.py : logique complète  │                 │
│   │  • vote/models.py : modèles Pydantic        │                 │
│   │  • 3 modes : sync, stream (SSE), async      │                 │
│   └──────────┬───────────────────────┬──────────┘                 │
│              │                       │                           │
│   ┌──────────┴──────┐   ┌───────────┴───────────┐                │
│   │  Persona Gen.   │   │   LLM Queue            │                │
│   │  • generator.py │   │   • Priorité HIGH/     │                │
│   │  • store.py     │   │     MEDIUM/LOW         │                │
│   │  • name_gen.    │   │   • Sérialisation GPU │                │
│   └─────────────────┘   └───────────┬───────────┘                │
│                                      │                            │
│   ┌──────────────────────────────────┴──────────────────────┐  │
│   │                      Personas System                       │  │
│   │  • Persistance SQLite (personas.db)                        │  │
│   │  • Génération nom réaliste (INSEE)                         │  │
│   │  • Validation qualité par LLM juge                        │  │
│   └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│   ┌──────────────────────┐   ┌───────────────────────┐         │
│   │   Profiles Registry    │   │  Event Log            │         │
│   │   • JSON auto-découverts│   │  • Audit sessions     │         │
│   │   • Distribution poids │   │  • SQLite (events.db) │         │
│   │   • Échantillonnage    │   │  • Cross-tab analysis │         │
│   └──────────────────────┘   └───────────────────────┘         │
│                                                                  │
└──────────────────────┬───────────────────────────────────────────┘
                       │
           ┌────────────┼────────────────┐
           ▼            ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   SQLite     │ │   Ollama     │ │   Settings   │
│  personas.db │ │   (:11434)   │ │  settings.json│
│  events.db   │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## Structure des fichiers

```text
voxpopulai/
├── README.md
├── CLAUDE.md
├── ARCHITECTURE.md
├── SPECS.md
├── ROADMAP.md
├── BEST_PRACTICES.md
├── pyproject.toml
├── .pre-commit-config.yaml
│
├── app/
│   ├── main.py                   # Entry point FastAPI
│   ├── config.py                 # Settings management
│   │
│   ├── api/                      # FastAPI routes
│   │   └── routes/
│   │       ├── vote.py           # Vote endpoints (sync/stream/async)
│   │       ├── personas.py       # Persona CRUD + generation
│   │       ├── profiles.py       # Profile listing
│   │       ├── history.py        # Session history + audit
│   │       ├── settings.py       # Configuration endpoints
│   │       └── models.py         # Ollama models listing
│   │
│   ├── frontend/                 # SPA vanilla JS
│   │   ├── index.html
│   │   ├── css/style.css
│   │   └── js/
│   │       ├── app.js            # Entry point
│   │       ├── router.js         # Hash routing
│   │       ├── api.js            # API client + SSE
│   │       ├── ui-helper.js
│   │       └── views/
│   │           ├── vote.js       # Vote UI
│   │           ├── personas.js   # Persona management
│   │           ├── history.js    # Session history
│   │           └── settings.js   # Configuration UI
│   │
│   ├── vote/                     # Voting logic
│   │   ├── orchestrator.py       # Main voting orchestration
│   │   └── models.py             # Pydantic models (Vote, Tally, Analysis)
│   │
│   ├── personas/                 # Persona system
│   │   ├── models.py             # Persona Pydantic model
│   │   ├── generator.py          # LLM-based generation
│   │   ├── store.py              # SQLite persistence
│   │   ├── name_generators.py    # French name generation (INSEE)
│   │   └── data/                 # Name data files
│   │       ├── prenoms.json
│   │       └── patronymes.json
│   │
│   ├── profiles/                 # Population profiles
│   │   ├── registry.py           # Profile loading
│   │   └── definitions/          # JSON profile definitions
│   │       ├── grand_public_france.json
│   │       ├── experts.json
│   │       ├── developpeurs.json
│   │       └── donjon_et_dragon.json
│   │
│   ├── llm/                      # LLM utilities
│   │   ├── queue.py              # Priority queue for Ollama
│   │   └── json_utils.py         # JSON extraction from responses
│   │
│   └── events/                   # Audit trail
│       └── event_log.py          # SQLite event logging
│
├── tests/                        # Test suite
│   └── (test files...)
│
└── data/                         # Runtime data
    ├── personas.db               # Generated personas
    ├── events.db                 # Session events
    └── settings.json             # App configuration
```

---

## Flux de données

### Vote complet (mode streaming SSE)

```text
SPA (frontend)
    │
    ├── API.stream("/api/vote/stream", body, onEvent)
    │   └── fetch POST → ReadableStream → parse SSE "data: {...}\n\n"
    │
    ▼
FastAPI StreamingResponse (text/event-stream)
    │
    ├── synthetic_vote_stream() generator
    │   │
    │   ├── Phase 1 — Personas (0-40%)
    │   │   ├── store.sample(profile, count) → personas existants
    │   │   └── si manquant → generator.generate_personas_iter()
    │   │       └── pour chaque persona :
    │   │           ├── registry.sample_attributes() → attributs pondérés
    │   │           ├── name_generator.generate() → nom réaliste
    │   │           ├── _create_persona() → appel LLM (retry + fallback)
    │   │           └── yield {"phase": "personas", "current": N, "total": T}
    │   │
    │   ├── Phase 2 — Votes (40-90%)
    │   │   └── pour chaque persona :
    │   │       ├── _cast_vote() → appel LLM avec system_prompt du persona
    │   │       ├── Position : OUI / NON / ABSTENTION
    │   │       ├── Raisonnement texte libre
    │   │       └── yield {"phase": "votes", "current": N, "total": T}
    │   │
    │   ├── Phase 3 — Analyse (90-100%)
    │   │   ├── yield {"phase": "analysis"}
    │   │   ├── _compute_tally() → décompte OUI/NON/ABSTENTION
    │   │   └── _analyze_votes() → appel LLM analyse qualitative
    │   │       ├── Position dominante + marge
    │   │       ├── Arguments clés (pour/contre)
    │   │       ├── Patterns démographiques
    │   │       └── Niveau consensus
    │   │
    │   └── yield {"phase": "done", "result": SyntheticVoteResult}
    │
    ▼
SPA : barre de progression déterministe + résultat final
```

### Génération de personas

```text
Profile Registry (JSON)
    │
    ├── Load profile definition
    │   └── dimensions : sexe, age, CSP, région...
    │   └── poids : distribution réaliste (INSEE)
    │
    ▼
Persona Generator
    │
    ├── Pour chaque persona à générer :
    │   │
    │   ├── 1. Sample attributes
    │   │   └── profile.sample() → {sexe: "F", age: "35-49", CSP: "Cadre"...}
    │   │
    │   ├── 2. Generate name
    │   │   ├── name_generator.sample_first_name(sexe, decade)
    │   │   └── name_generator.sample_last_name()
    │   │   └── → "Marie Dubois"
    │   │
    │   ├── 3. LLM Generation
    │   │   ├── Prompt : "Crée un persona français..."
    │   │   ├── Input : attributs + nom
    │   │   └── Output JSON : {background, system_prompt, values...}
    │   │
    │   ├── 4. Quality validation (optionnel)
    │   │   ├── Judge model évalue la qualité
    │   │   ├── Si rejeté → retry (max 3)
    │   │   └── Sinon → persistance
    │   │
    │   └── 5. Persist to SQLite
    │       └── INSERT INTO personas (id, profile_name, name, attributes...)
    │
    ▼
personas.db (SQLite)
```

### Audit et historique

```text
Vote Session
    │
    ├── Event Log (SQLite events.db)
    │   ├── collaboration_start → session_id, timestamp, question
    │   ├── persona_vote → persona_id, position, reasoning
    │   ├── ... (repeat pour chaque vote)
    │   └── collaboration_end → tally, analysis
    │
    ▼
History API
    │
    ├── GET /api/history/ → liste sessions paginée
    ├── GET /api/history/{id} → session complète (reconstruction)
    └── GET /api/history/{id}/audit → cross-tab par attribut
        │
        └── Crosstabulation :
            ├── Par sexe : F {oui: 45, non: 12...}, M {...}
            ├── Par age : 18-24 {...}, 25-34 {...}
            └── Par CSP : Cadre {...}, Ouvrier {...}
```

---

## Persistance

| Donnée | Format | Emplacement | Description |
| ------ | ------ | ----------- | ----------- |
| Personas | SQLite | `data/personas.db` | Personas générés avec attributs et prompts |
| Events | SQLite | `data/events.db` | Audit trail des sessions de vote |
| Settings | JSON | `data/settings.json` | Configuration modèles et paramètres |
| Profils | JSON | `app/profiles/definitions/` | Définitions des profils population |
| Noms INSEE | JSON | `app/personas/data/` | Données prénoms et patronymes |

### Schémas SQLite

**personas.db :**
```sql
CREATE TABLE personas (
    id TEXT PRIMARY KEY,
    profile_name TEXT NOT NULL,
    name TEXT NOT NULL,
    attributes TEXT NOT NULL,  -- JSON
    system_prompt TEXT NOT NULL,
    background TEXT NOT NULL,
    model TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX idx_personas_profile ON personas (profile_name);
```

**events.db :**
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    type TEXT NOT NULL,
    collaboration_id TEXT,
    workspace TEXT,
    agent TEXT,
    model TEXT,
    data TEXT NOT NULL  -- JSON
);
CREATE INDEX idx_events_collab_id ON events (collaboration_id);
CREATE INDEX idx_events_type_ts ON events (type, timestamp);
```

---

## Sécurité

| Mécanisme | Implémentation |
|-----------|----------------|
| Injection SQL | Requêtes paramétrées uniquement (jamais de string interpolation) |
| Validation | Pydantic models pour toutes les entrées API |
| Secrets | Variables d'environnement ou settings.json (non versionné) |
| CORS | Configurable, restrictions en production |
| Path traversal | Pas d'accès filesystem depuis l'API (tout en DB) |

---

## Dépendances externes

```text
VoxPopulAI (:8000) ──── Ollama (:11434)
                           └── Modèles LLM pour :
                               ├── Génération personas
                               ├── Vote individuel
                               └── Analyse résultats
```

**Ollama** est le seul service externe obligatoire. Tout est local (SQLite, pas de Redis ni de services cloud).

---

## Modèles de données principaux

### Persona

```python
class Persona(BaseModel):
    id: str                          # UUID v4
    profile_name: str               # ex: "grand_public_france"
    name: str                       # "Marie Dubois"
    attributes: Dict[str, str]      # {sexe: "F", age: "35-49", CSP: "Cadre"...}
    system_prompt: str               # Prompt système pour le LLM
    background: str                  # Background textuel
    model: str                       # LLM utilisé pour la génération
    created_at: datetime
```

### Vote

```python
class Vote(BaseModel):
    persona: Persona                 # Référence au persona
    position: Literal["oui", "non", "abstention"]
    reasoning: str                   # Raisonnement détaillé
```

### VoteResult

```python
class SyntheticVoteResult(BaseModel):
    profile_name: str
    question: str
    persona_count: int
    tally: VoteTally                 # {oui: N, non: N, abstention: N}
    analysis: VoteAnalysis           # Insights qualitatifs
    disclaimer: str                  # Avertissement simulation
    collaboration_id: Optional[str]  # UUID pour audit
```

---

## Stratégie de file d'attente LLM

```text
┌─────────────────────────────────────────┐
│           LLM Queue                     │
│  ┌─────────────────────────────────┐   │
│  │ Priority Queue (asyncio)      │   │
│  │                               │   │
│  │ HIGH    │ Vote streaming      │   │
│  │ MEDIUM  │ Analyse résultats   │   │
│  │ LOW     │ Bulk persona gen.   │   │
│  └─────────────────────────────────┘   │
│              │                          │
│              ▼                          │
│  ┌──────────────────────────────┐    │
│  │ Worker (asyncio)             │    │
│  │                              │    │
│  │ While queue not empty:       │    │
│  │   1. Pop highest priority    │    │
│  │   2. Call Ollama API         │    │
│  │   3. Return result           │    │
│  │   4. Process next            │    │
│  └──────────────────────────────┘    │
└─────────────────────────────────────────┘
```

La file d'attente sérialise les appels LLM pour éviter la surcharge GPU.
