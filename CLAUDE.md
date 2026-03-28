# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VoxPopulAI is a **synthetic population voting simulator** powered by LLMs. It generates artificial personas based on demographic profiles, has them vote independently on questions, and analyzes results with qualitative insights.

**Extracted from ATEAM** — this is the standalone voting feature isolated from the larger multi-agent system.

---

## Build & Run

```bash
# Setup environment
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run development server
python -m app.main

# Server starts on http://localhost:8000
# - API docs: http://localhost:8000/docs
# - Frontend: http://localhost:8000
```

The application uses FastAPI with auto-reload (uvicorn `--reload`). Static files (SPA) are served by FastAPI from `app/frontend/`.

---

## Testing

```bash
# All tests (default markers)
pytest tests/ -v

# Specific test file
pytest tests/test_vote.py -v

# Specific test
pytest tests/test_vote.py::test_synthetic_vote -v

# Fail fast (stop on first failure)
pytest tests/ -v -x

# With coverage
pytest tests/ --cov=app --cov-fail-under=80
```

### Test markers

| Marker | Description | Run by default |
|--------|-------------|--------------|
| *(none)* | Unit tests | Yes |
| `slow` | Tests with LLM calls (slow) | No |

Configure in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
addopts = ["-v", "--tb=short", "-m", "not slow"]
```

---

## Architecture

**API Layer** — `app/api/routes/`:
- `vote.py`: Voting endpoints (sync, stream, async)
- `personas.py`: Persona management (generate, list, stats)
- `profiles.py`: Population profiles listing
- `history.py`: Session history and audit
- `settings.py`: App configuration

**Services Layer** — `app/`:
- `vote/orchestrator.py`: Voting orchestration logic
- `vote/models.py`: Vote data models (Pydantic)
- `personas/generator.py`: LLM-based persona generation with quality validation
- `personas/store.py`: SQLite persistence for personas
- `personas/name_generators.py`: French realistic names (INSEE data)
- `profiles/registry.py`: Profile loading and management
- `llm/queue.py`: Priority queue for Ollama calls
- `llm/json_utils.py`: JSON extraction from LLM responses
- `events/event_log.py`: SQLite session audit trail

**Frontend** — `app/frontend/`:
- Vanilla JS SPA with hash-based routing
- `js/views/`: vote.js, personas.js, history.js, settings.js
- Real-time progress via Server-Sent Events (SSE)

**Data** — `data/`:
- `personas.db`: SQLite with generated personas
- `events.db`: SQLite session events (audit trail)
- `settings.json`: App configuration (models, temperatures)

---

## Key Components

### Voting System

**Flow:**
1. Load profile → generate/load personas from store
2. Each persona votes (position + reasoning) via LLM
3. Compute tally (counts + percentages)
4. LLM analyzes results (arguments, patterns, consensus)

**Execution modes:**
- **Sync**: Blocking request, returns complete result
- **Stream**: SSE with progress events (personas → votes → analysis)
- **Async**: Background execution with status polling

### Persona Generation

**Process:**
1. Sample attribute combination from profile weights
2. Generate realistic French name (gender/decade-based)
3. LLM creates background and system prompt
4. Judge model validates quality (optional)
5. Persist to SQLite

**Quality validation:**
- Retry logic for JSON parsing failures
- Judge model rejects low-quality personas
- Configurable max retries in settings

### LLM Queue

Priority-based queue for Ollama API calls:
- `HIGH`: User-facing operations (voting)
- `MEDIUM`: Background tasks
- `LOW`: Bulk persona generation

Prevents GPU overload by serializing requests.

---

## Configuration

**Environment variables** (optional):
- `DATA_DIR`: Runtime data directory (default: `./data`)
- `PERSONA_DB_PATH`: Persona database path
- `EVENTS_DB_PATH`: Events database path

**Settings** (`data/settings.json`):
```json
{
  "synthetic": {
    "generation_model": "qwen3:14b",
    "generation_temperature": 0.8,
    "judge_model": "",
    "judge_temperature": 0.1,
    "judge_max_retries": 2,
    "persona_models": ["qwen3:14b"],
    "analysis_model": "qwen3:14b"
  },
  "ollama": {
    "num_ctx": 8192,
    "temperature": 0.8,
    "top_k": 40,
    "top_p": 0.9
  }
}
```

---

## Development Process

**Golden rule**: All development must be tied to a GitHub issue.

### Workflow

1. Create or take an issue on GitHub
2. Create a branch: `git checkout -b <issue>-<description>`
3. Develop with pre-commit hooks active (`pre-commit install`)
4. Run tests: `pytest tests/ -v`
5. Commit with conventional format: `feat(scope): description`
6. Link PR to issue (`closes #N`)
7. After merge: update `ROADMAP.md`

### Conventional Commits

```bash
feat(vote): add async voting endpoint
fix(personas): handle json parsing errors
docs(api): update endpoint documentation
refactor(llm): extract json utilities
test(vote): add edge case tests
```

### PR Checklist

- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Pre-commit OK (`pre-commit run --all-files`)
- [ ] PR linked to GitHub issue (`closes #N`)
- [ ] No business logic in `api/routes/` (delegate to services)
- [ ] Documentation updated if needed

See `BEST_PRACTICES.md` for complete standards.

---

## Key Conventions

- **Language**: Project docs and code comments in French; code identifiers in English
- **Models**: Pydantic for all data validation
- **Async**: Use `async/await` for all I/O operations (LLM calls, DB)
- **Database**: SQLite with parameterized queries (NEVER string interpolation)
- **Error handling**: Specific exceptions with context; graceful degradation
- **Frontend**: Event delegation for dynamic content; cleanup listeners

---

## Common Tasks

### Add a new population profile

1. Create JSON in `app/profiles/definitions/<name>.json`
2. Follow structure of existing profiles (see `grand_public_france.json`)
3. Profile auto-discovered on startup

### Debug persona generation

```python
# Enable verbose logging in generator.py
logger.info("generating_persona", attributes=attrs, attempt=attempt)

# Check generated personas
sqlite3 data/personas.db "SELECT * FROM personas LIMIT 5;"
```

### Monitor Ollama queue

The queue has basic logging. For debugging:
```python
# In llm/queue.py
logger.info("queue_submit", priority=priority, model=model, queue_size=len(self.queue))
```

### Test with specific model

Change in Settings UI or directly edit `data/settings.json`:
```json
{
  "synthetic": {
    "persona_models": ["llama3:8b"]
  }
}
```

---

## Troubleshooting

### Ollama connection errors

- Verify Ollama is running: `ollama list`
- Check host URL (default: `http://localhost:11434`)
- Ensure model is pulled: `ollama pull qwen3:14b`

### JSON parsing failures

- Check `llm/json_utils.py` extraction logic
- Enable judge model for stricter validation
- Review persona prompts in `generator.py`

### Database locked errors

SQLite file locking with concurrent writes:
- Use connection pooling (not yet implemented)
- Reduce concurrent persona generation
- Consider migrating to PostgreSQL for high concurrency
