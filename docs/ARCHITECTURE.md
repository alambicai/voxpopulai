# Architecture

## Overview

VoxPopulAI is a synthetic population voting simulator powered by Large Language Models (LLMs). It enables the simulation of voting scenarios by generating artificial personas based on demographic profiles, having these personas vote on questions, and analyzing results with qualitative insights.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client (Browser)                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │  Vote   │  │ Personas│  │ History │  │Settings │         │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘         │
│       └─────────────┴─────────────┴─────────────┘              │
│                        │                                     │
│                    REST API / SSE                            │
└────────────────────────┼────────────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌─────────────────────┼─────────────────────────────────┐  │
│  │                 API Layer                              │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │  │
│  │  │  Vote   │ │Personas │ │ History │ │ Settings│    │  │
│  │  │ Routes  │ │ Routes  │ │ Routes  │ │ Routes  │    │  │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘    │  │
│  └───────┼───────────┼───────────┼───────────┼─────────┘  │
│          │           │           │           │              │
│  ┌───────┴───────────┴───────────┴───────────┴─────────┐  │
│  │              Business Logic Layer                     │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Voting    │  │   Persona   │  │    Event    │  │  │
│  │  │ Orchestrator│  │  Generator  │  │     Log     │  │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │  │
│  └─────────┼────────────────┼────────────────┼────────┘  │
│            │                │                │             │
│  ┌─────────┴────────────────┴────────────────┴─────────┐  │
│  │              Infrastructure Layer                     │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │  LLM Queue  │  │ Profile     │  │  Settings   │  │  │
│  │  │  (Ollama)   │  │  Registry   │  │   Store     │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────────────┐
│                   Data Layer                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ personas.db │  │  events.db  │  │   settings.json     │  │
│  │  (SQLite)   │  │   (SQLite)  │  │       (JSON)        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────────────┐
│                   External Services                          │
│                    Ollama (LLM API)                            │
└──────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Layer (`app/api/routes/`)

RESTful API endpoints organized by domain:

- **Vote Routes** (`vote.py`): Orchestrates synthetic voting sessions
- **Personas Routes** (`personas.py`): Manages generated personas
- **Profiles Routes** (`profiles.py`): Lists available population profiles
- **History Routes** (`history.py`): Provides session audit and reconstruction
- **Settings Routes** (`settings.py`): Manages application configuration
- **Models Routes** (`models.py`): Lists available Ollama models

### 2. Business Logic Layer

#### Voting System (`app/vote/`)

The `orchestrator.py` implements the core voting workflow:

1. **Persona Generation/Loading**: Load existing personas or generate new ones from a profile
2. **Individual Voting**: Each persona votes independently with position (oui/non/abstention) and reasoning
3. **Tally Computation**: Aggregate votes into counts and percentages
4. **Qualitative Analysis**: LLM analyzes results for key arguments and demographic patterns

Supports three execution modes:
- **Synchronous**: Blocking request, returns complete result
- **Streaming**: Server-Sent Events with progress updates
- **Asynchronous**: Background execution with status polling

#### Persona System (`app/personas/`)

Three main components:

- **`generator.py`**: LLM-based persona creation with quality validation
  - Samples attribute combinations from profile weights
  - Generates rich persona (name, background, values, vision, traits)
  - Uses "judge" model for quality validation with retry logic
  
- **`store.py`**: SQLite persistence layer for personas
  - CRUD operations
  - Random sampling for voting sessions
  - Statistics and distribution queries
  
- **`name_generators.py`**: Realistic name generation for French personas
  - Uses INSEE demographic data
  - Considers gender, birth decade, and religion context

#### Events System (`app/events/`)

`event_log.py` provides audit trail functionality:
- SQLite-based event storage
- Collaboration tracking (start/end events)
- Session reconstruction from event stream
- Cross-tabulation audit for demographic analysis

### 3. Infrastructure Layer

#### LLM Integration (`app/llm/`)

- **`queue.py`**: Priority queue for Ollama API calls
  - Serializes GPU access to prevent overload
  - Priority levels: HIGH, MEDIUM, LOW
  - Async worker with thread pool executor
  
- **`json_utils.py`**: LLM response parsing utilities
  - Strips `<thinking>` blocks from reasoning models
  - Extracts JSON from markdown code blocks
  - Fixes malformed JSON (unescaped quotes, etc.)

#### Profile Registry (`app/profiles/`)

`registry.py` manages population profile definitions:
- Loads JSON profile definitions from `definitions/`
- Provides weighted random sampling for persona generation
- Four built-in profiles: grand_public_france, experts, developpeurs, donjon_et_dragon

### 4. Data Layer

#### personas.db
SQLite database storing generated personas with schema:
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
```

#### events.db
SQLite database for audit trail:
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
```

#### settings.json
JSON file storing application configuration:
- Synthetic vote settings (models, temperatures, retries)
- Ollama runtime parameters (context window, sampling params)

## Data Flow

### Voting Session Flow

```
┌──────────┐     ┌──────────────┐     ┌─────────────────┐
│  Client  │────▶│ POST /vote/  │────▶│   Orchestrator  │
└──────────┘     └──────────────┘     └────────┬────────┘
                                               │
                    ┌──────────────────────────┼──────────┐
                    │                          │          │
           ┌────────▼────────┐        ┌───────▼───────┐  │
           │  Profile Registry│        │  Persona Store │  │
           │  (Load Definition)│        │  (Load/Sample) │  │
           └────────┬────────┘        └───────┬───────┘  │
                    │                          │          │
                    └──────────┬───────────────┘          │
                               │                          │
                    ┌──────────▼──────────┐               │
                    │   Persona Generator │               │
                    │  (if not in store)  │               │
                    └──────────┬──────────┘               │
                               │                          │
                    ┌──────────▼──────────┐               │
                    │     LLM Queue       │               │
                    │   (Ollama API)      │               │
                    └──────────┬──────────┘               │
                               │                          │
                               ▼                          ▼
                    ┌─────────────────────────────────────┐
                    │      Individual Voting (Parallel)   │
                    │  ┌─────────┐ ┌─────────┐ ┌────────┐ │
                    │  │Persona 1│ │Persona 2│ │  ...   │ │
                    │  └────┬────┘ └────┬────┘ └───┬────┘ │
                    └───────┼───────────┼──────────┼──────┘
                            └───────────┴──────────┘
                                          │
                               ┌──────────▼──────────┐
                               │    Vote Tally       │
                               │  (Aggregate Results) │
                               └──────────┬──────────┘
                                          │
                               ┌──────────▼──────────┐
                               │   LLM Analysis      │
                               │ (Qualitative Insights)│
                               └──────────┬──────────┘
                                          │
                               ┌──────────▼──────────┐
                               │   Event Log         │
                               │ (Audit Trail)       │
                               └──────────┬──────────┘
                                          │
                               ┌──────────▼──────────┐
                               │  Response to Client  │
                               └─────────────────────┘
```

### Persona Generation Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Profile    │────▶│   Sample     │────▶│  Attribute Combo │
│  Definition  │     │   Weights    │     │  (e.g., age, CSP) │
└──────────────┘     └──────────────┘     └────────┬─────────┘
                                                   │
                          ┌────────────────────────┘
                          │
               ┌──────────▼──────────┐
               │  Name Generator     │
               │  (Demographic Data) │
               └──────────┬──────────┘
                          │
               ┌──────────▼──────────┐
               │  LLM Generator      │
               │  (Persona Prompt)    │
               └──────────┬──────────┘
                          │
               ┌──────────▼──────────┐
               │  JSON Extraction    │
               │  (Parse Response)   │
               └──────────┬──────────┘
                          │
               ┌──────────▼──────────┐
               │  Quality Judge      │
               │  (Validation)       │
               └──────────┬──────────┘
                          │
               ┌──────────▼──────────┐
               │  Persona Store      │
               │  (Persist)          │
               └─────────────────────┘
```

## Authentication & Security

- **No authentication layer**: The application is designed for local/single-user use
- **CORS**: Configured for development (localhost origins)
- **Input validation**: Pydantic models validate all API inputs
- **No secrets in code**: Environment variables for configuration

## Frontend Architecture

Vanilla JavaScript SPA (Single Page Application):

```
┌─────────────────────────────────────────┐
│              index.html                  │
│  ┌─────────────────────────────────────┐│
│  │          JavaScript Layer            ││
│  │  ┌─────────┐ ┌─────────┐ ┌────────┐││
│  │  │  app.js │ │router.js│ │ api.js │││
│  │  │(Entry)  │ │(Routing)│ │(Client)│││
│  │  └────┬────┘ └────┬────┘ └───┬────┘││
│  │       └─────────────┴─────────┘      ││
│  │                │                     ││
│  │       ┌────────▼────────┐            ││
│  │       │   View Layer     │            ││
│  │  ┌────┴────┐ ┌────┴────┐ ┌────┴───┐ ││
│  │  │ vote.js │ │personas.│ │history.│ ││
│  │  │(Voting) │ │   js    │ │  js    │ ││
│  │  └─────────┘ └─────────┘ └────────┘ ││
│  │       ┌─────────────────┐            ││
│  │       │  settings.js    │            ││
│  │       │  (Configuration) │            ││
│  │       └─────────────────┘            ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │           CSS Layer                  ││
│  │       style.css (Dark Theme)       ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

### Key Frontend Patterns

- **Hash-based routing**: URL fragments determine current view
- **Event-driven updates**: API responses trigger UI updates
- **Streaming support**: Server-Sent Events for real-time progress
- **State management**: Simple object-based state in app.js

## Deployment Architecture

### Development

```
┌────────────────────────────────────────┐
│           Local Machine                 │
│  ┌──────────┐      ┌──────────────────┐ │
│  │  Ollama  │◄────►│  VoxPopulAI API  │ │
│  │ (GPU)    │      │  (Uvicorn/FastAPI)│ │
│  └──────────┘      └──────────────────┘ │
│                           │              │
│                    ┌──────┴──────┐       │
│                    │  Browser    │       │
│                    │  (Frontend) │       │
│                    └─────────────┘       │
└────────────────────────────────────────┘
```

### Production (Recommended)

```
┌────────────────────────────────────────┐
│           Docker Compose               │
│  ┌──────────┐      ┌──────────────────┐│
│  │  Ollama  │◄────►│  VoxPopulAI API  ││
│  │ Service  │      │   Service        ││
│  └──────────┘      └──────────────────┘│
│                           │            │
│  ┌────────────────────────┴──────────┐ │
│  │        Reverse Proxy (Nginx)       │ │
│  │    (Static files + API proxy)      │ │
│  └────────────────────────────────────┘ │
└────────────────────────────────────────┘
```

## Scaling Considerations

### Current Limitations

- **Single-node Ollama**: GPU-bound inference
- **SQLite databases**: File-based, not distributed
- **In-memory queue**: No persistence across restarts

### Potential Improvements

1. **Model serving**: Scale Ollama horizontally with model replication
2. **Database**: Migrate to PostgreSQL for concurrent access
3. **Queue**: Implement Redis or RabbitMQ for distributed task processing
4. **Caching**: Add Redis layer for persona and vote result caching

## Monitoring & Observability

Currently minimal:
- Event log provides audit trail
- LLM queue has basic logging
- No metrics collection or alerting

Recommendations:
- Add structured logging (JSON format)
- Implement Prometheus metrics
- Add health check endpoints
- Monitor LLM API latency and error rates
