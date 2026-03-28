# Best Practices

## Development Workflow

### Git Workflow

1. **Branch from `dev`**: All feature branches originate from the `dev` branch
2. **Branch naming**: `<issue_id>-<short-description>` (e.g., `42-add-user-auth`)
3. **Commits**: Use Conventional Commits format:
   - `feat(scope): description` - New feature
   - `fix(scope): description` - Bug fix
   - `refactor(scope): description` - Code refactoring
   - `docs(scope): description` - Documentation changes
   - `test(scope): description` - Test additions/changes
   - `chore(scope): description` - Tooling, dependencies, config
4. **Pull Requests**:
   - Create as draft initially: `gh pr create --draft --base dev --fill`
   - Mark "Ready for review" when complete
   - Require at least one peer review
   - CI must pass before merge
5. **Merge**: Squash merge to keep history clean
6. **Language**: All commits, code, comments, and documentation in **English**

### Code Quality Checklist

Before marking a PR as ready:

- [ ] No commented-out code (use Git history instead)
- [ ] No debug print statements or logging left behind
- [ ] No hardcoded secrets or API keys
- [ ] Unused imports removed
- [ ] Code formatted with Ruff
- [ ] All tests pass
- [ ] Documentation updated (SPECS.md, ARCHITECTURE.md if applicable)

### Pre-commit Hooks

Required hooks are configured in `.pre-commit-config.yaml`:

```bash
# Install hooks
pip install pre-commit
pre-commit install

# Run on all files
pre-commit run --all-files
```

Hooks include:
- Trailing whitespace removal
- End of file fixer
- YAML validation
- Large files check (max 500KB)
- Merge conflict detection
- Private key detection

---

## Code Style

### Python Style Guide

**Formatter**: Ruff (configured in `pyproject.toml`)

**Key settings:**
- Line length: 100 characters
- Target Python version: 3.10+
- Import sorting enabled

**Patterns to follow:**

```python
# Good: Type hints
from typing import Optional, List
def get_persona(persona_id: str) -> Optional[Persona]:
    ...

# Good: Pydantic models for data validation
from pydantic import BaseModel, Field

class VoteRequest(BaseModel):
    profile_name: str
    question: str
    count: int = Field(default=100, ge=1, le=1000)

# Good: Async/await for I/O operations
async def generate_persona(profile: Profile) -> Persona:
    async with aiohttp.ClientSession() as session:
        ...

# Good: Descriptive variable names
persona_count = len(personas)  # Not: pc = len(p)
is_vote_complete = all(v.position for v in votes)  # Not: vc = all(...)

# Good: Constants at module level
MAX_PERSONA_GENERATION_RETRIES = 3
DEFAULT_VOTE_COUNT = 100

# Bad: Avoid
x = 1  # Unclear variable name
def func(a, b):  # Missing type hints
    return a + b
```

### Import Organization

```python
# 1. Standard library
import json
from datetime import datetime
from typing import Dict, List, Optional

# 2. Third-party packages
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 3. First-party (app)
from app.config import settings
from app.personas.models import Persona
```

Ruff's isort configuration handles this automatically.

### Error Handling

```python
# Good: Specific exceptions with context
from fastapi import HTTPException

def get_profile(name: str) -> Profile:
    try:
        return registry.load(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Profile '{name}' not found")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid profile format: {e}")

# Good: Graceful degradation
async def llm_call_with_fallback(prompt: str) -> str:
    try:
        return await primary_llm.generate(prompt)
    except LLMError:
        logger.warning("Primary LLM failed, trying fallback")
        return await fallback_llm.generate(prompt)
```

---

## Architecture Patterns

### Dependency Injection

Use FastAPI's dependency injection for shared resources:

```python
from fastapi import Depends

async def get_persona_store() -> PersonaStore:
    return PersonaStore(settings.persona_db_path)

@app.get("/api/personas/")
async def list_personas(store: PersonaStore = Depends(get_persona_store)):
    return store.list_all()
```

### Repository Pattern

Data access is abstracted through repository classes:

```python
# app/personas/store.py
class PersonaStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_by_id(self, persona_id: str) -> Optional[Persona]:
        ...
    
    def sample(self, profile: str, count: int) -> List[Persona]:
        ...
    
    def save(self, persona: Persona) -> None:
        ...
```

### Service Layer

Business logic lives in service modules, not routes:

```python
# app/vote/orchestrator.py (service layer)
async def synthetic_population_vote(
    profile_name: str,
    question: str,
    count: int,
    models: List[str]
) -> SyntheticVoteResult:
    # Orchestration logic here
    ...

# app/api/routes/vote.py (thin controller)
@app.post("/api/vote/")
async def create_vote(request: VoteRequest):
    result = await synthetic_population_vote(
        request.profile_name,
        request.question,
        request.count,
        request.models
    )
    return result
```

---

## LLM Integration Best Practices

### Prompt Engineering

1. **Be explicit**: Clear instructions, expected output format
2. **Provide examples**: Few-shot prompting for complex tasks
3. **Use structured output**: JSON mode or explicit JSON instructions
4. **Keep prompts focused**: One task per prompt
5. **Version prompts**: Track prompt changes with performance impact

**Example persona generation prompt structure:**
```python
PERSONA_GENERATION_PROMPT = """
Create a realistic persona based on these demographic attributes:
{attributes}

Name: {name}

Generate:
1. Background (2-3 paragraphs about their life, values, experiences)
2. System prompt (how they should respond as this persona)

Return JSON:
{
  "background": "...",
  "system_prompt": "..."
}
"""
```

### JSON Extraction

LLM responses may include markdown or malformed JSON. Use the utility:

```python
from app.llm.json_utils import extract_json

# Handles markdown code blocks, thinking tags, common JSON errors
parsed = extract_json(llm_response_text)
```

### Retry Logic

Always implement retries for LLM calls:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(LLMError)
)
async def generate_with_retry(prompt: str) -> str:
    return await llm.generate(prompt)
```

### Queue Management

The LLM queue prevents GPU overload:

```python
from app.llm.queue import llm_queue, Priority

# HIGH: User-facing operations
# MEDIUM: Background tasks
# LOW: Bulk operations

result = await llm_queue.submit(
    prompt="...",
    priority=Priority.HIGH,
    model="qwen3:14b"
)
```

### Model Selection Guidelines

| Task | Recommended Model | Temperature |
|------|-------------------|-------------|
| Persona generation | qwen3:14b | 0.8 |
| Quality validation | qwen3:14b | 0.1 |
| Voting | qwen3:14b, llama3:8b | 0.7 |
| Result analysis | qwen3:14b | 0.5 |

---

## Testing

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_personas.py
│   ├── test_vote.py
│   └── test_profiles.py
├── integration/
│   └── test_api.py
└── fixtures/
    └── sample_profiles.json
```

### Test Naming

```python
# Pattern: test_<function>_<scenario>
def test_vote_tally_with_all_positions():
    ...

def test_persona_generation_retries_on_failure():
    ...

def test_get_profile_returns_404_for_missing():
    ...
```

### Fixtures

```python
# tests/conftest.py
import pytest
from app.profiles.registry import ProfileRegistry

@pytest.fixture
def sample_profile():
    return {
        "name": "test",
        "description": "Test profile",
        "attributes": {
            "age": {"values": {"18-24": {"weight": 100}}}
        }
    }

@pytest.fixture
def profile_registry(tmp_path):
    return ProfileRegistry(tmp_path)
```

### Async Testing

```python
import pytest

@pytest.mark.asyncio
async def test_async_vote_generation():
    result = await orchestrator.synthetic_population_vote(
        profile_name="test",
        question="Test question?",
        count=5
    )
    assert result.persona_count == 5
```

### Mocking External Services

```python
from unittest.mock import Mock, patch

@patch("app.llm.queue.llm_queue.submit")
async def test_vote_with_mocked_llm(mock_submit):
    mock_submit.return_value = '{"position": "oui", "reasoning": "Test"}'
    
    result = await orchestrator.synthetic_population_vote(...)
    
    assert mock_submit.called
    assert result.tally.oui > 0
```

---

## Database Best Practices

### SQLite Patterns

```python
# Connection management with context managers
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db_connection(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Parameterized queries (NEVER use string interpolation)
def get_persona(persona_id: str) -> Optional[Persona]:
    with get_db_connection(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT * FROM personas WHERE id = ?",
            (persona_id,)  # Tuple with trailing comma
        )
        row = cursor.fetchone()
        return Persona(**row) if row else None
```

### Schema Migrations

For now, schemas are created on startup. For production:

1. Use Alembic for migration management
2. Version all schema changes
3. Test migrations against production-like data

---

## Frontend Best Practices

### JavaScript Patterns

```javascript
// Module pattern with explicit exports
const ApiClient = {
    async getPersonas(profile, options = {}) {
        const params = new URLSearchParams({
            profile,
            limit: options.limit || 50,
            offset: options.offset || 0
        });
        
        const response = await fetch(`/api/personas/?${params}`);
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        return response.json();
    }
};

export default ApiClient;
```

### Event Handling

```javascript
// Delegate events for dynamic content
document.addEventListener('click', (e) => {
    if (e.target.matches('.delete-persona')) {
        const personaId = e.target.dataset.id;
        handleDelete(personaId);
    }
});

// Cleanup event listeners
function createModal() {
    const modal = document.createElement('div');
    const closeHandler = () => modal.remove();
    
    modal.querySelector('.close').addEventListener('click', closeHandler);
    
    // Return cleanup function
    return {
        element: modal,
        destroy() {
            modal.querySelector('.close').removeEventListener('click', closeHandler);
            modal.remove();
        }
    };
}
```

### SSE (Server-Sent Events) Handling

```javascript
async function streamVote(request) {
    const eventSource = new EventSource(`/api/vote/stream`, {
        method: 'POST',
        body: JSON.stringify(request)
    });
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
            case 'progress':
                updateProgress(data.percentage);
                break;
            case 'persona_vote':
                addVoteToTable(data);
                break;
            case 'complete':
                showResults(data);
                eventSource.close();
                break;
            case 'error':
                showError(data.message);
                eventSource.close();
                break;
        }
    };
    
    eventSource.onerror = () => {
        showError('Connection lost');
        eventSource.close();
    };
}
```

---

## Security Best Practices

### Input Validation

All inputs validated through Pydantic models:

```python
from pydantic import BaseModel, Field, validator

class VoteRequest(BaseModel):
    profile_name: str
    question: str
    count: int = Field(default=100, ge=1, le=1000)
    
    @validator('question')
    def validate_question(cls, v):
        if len(v) > 1000:
            raise ValueError('Question too long (max 1000 chars)')
        return v.strip()
```

### Environment Variables

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    data_dir: str = "./data"
    persona_db_path: str = "./data/personas.db"
    
    class Config:
        env_prefix = ""  # No prefix for env vars

settings = Settings()
```

### No Secrets in Code

```bash
# .gitignore
data/
*.db
.env
settings.json
```

### CORS Configuration

```python
# Restrict origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Not ["*"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

---

## Performance Optimization

### Database

- Add indexes for frequently queried columns
- Use connection pooling for concurrent requests
- Cache expensive queries (Redis/memcached)

### LLM Calls

- Batch similar requests when possible
- Cache persona generation results
- Use lower temperature for deterministic tasks
- Implement request deduplication

### Frontend

- Lazy load persona data (pagination)
- Debounce input handlers
- Use CSS transforms for animations
- Minimize DOM updates

---

## Documentation

### Code Documentation

```python
def calculate_tally(votes: List[Vote]) -> VoteTally:
    """
    Calculate vote tally from a list of votes.
    
    Args:
        votes: List of Vote objects with position and reasoning
        
    Returns:
        VoteTally with counts and percentages for each position
        
    Raises:
        ValueError: If votes list is empty
        
    Example:
        >>> votes = [Vote(position="oui", ...), Vote(position="non", ...)]
        >>> tally = calculate_tally(votes)
        >>> assert tally.oui == 1
    """
    if not votes:
        raise ValueError("Cannot calculate tally for empty vote list")
    
    # Implementation...
```

### README Updates

Update README.md when:
- New features added
- Setup instructions change
- Dependencies updated
- Architecture changes

### API Documentation

FastAPI auto-generates OpenAPI docs at `/docs`. Ensure:
- All routes have descriptive docstrings
- Pydantic models have field descriptions
- Response models are explicitly defined

---

## Common Pitfalls

### LLM Integration

- **Assuming perfect JSON**: Always validate and have fallback parsing
- **Ignoring token limits**: Monitor context window usage
- **No timeout handling**: LLM calls can hang; implement timeouts
- **Blocking the event loop**: Use async/await properly

### Database

- **Connection leaks**: Always use context managers
- **N+1 queries**: Batch queries when possible
- **No transaction handling**: Use transactions for multi-step operations

### Async Code

- **Mixing sync and async**: Use `asyncio.to_thread()` for CPU-bound tasks
- **Forgetting await**: Enable mypy to catch missing awaits
- **Race conditions**: Use locks for shared mutable state

### Frontend

- **Memory leaks**: Clean up event listeners and timers
- **XSS vulnerabilities**: Sanitize user input before DOM insertion
- **Race conditions**: Cancel pending requests on new user actions
