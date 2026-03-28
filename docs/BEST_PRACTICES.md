# Bonnes Pratiques de Développement

Standards de qualité pour le projet VoxPopulAI.

---

## 1. Structure du Projet

### Architecture cible

```
voxpopulai/
├── app/
│   ├── api/                      # FastAPI backend (point d'entrée)
│   │   └── routes/
│   │       ├── vote.py           # Endpoints vote
│   │       ├── personas.py       # Endpoints personas
│   │       ├── profiles.py       # Endpoints profils
│   │       ├── history.py        # Endpoints historique
│   │       ├── settings.py       # Endpoints configuration
│   │       └── models.py         # Endpoints modèles Ollama
│   │
│   ├── frontend/                 # SPA vanilla JS
│   │   ├── index.html
│   │   ├── css/
│   │   └── js/
│   │       ├── app.js            # Entry point
│   │       ├── router.js         # Hash routing
│   │       ├── api.js            # API client + SSE
│   │       └── views/            # Vote, Personas, History, Settings
│   │
│   ├── vote/                     # Logique métier vote
│   │   ├── orchestrator.py       # Orchestration complète
│   │   └── models.py             # Modèles Pydantic
│   │
│   ├── personas/                 # Système personas
│   │   ├── generator.py          # Génération LLM
│   │   ├── store.py              # SQLite persistence
│   │   ├── name_generators.py    # Génération noms INSEE
│   │   ├── models.py             # Modèle Persona
│   │   └── data/                 # Données prénoms/patronymes
│   │
│   ├── profiles/                 # Profils population
│   │   ├── registry.py           # Chargement JSON
│   │   └── definitions/          # Fichiers profils
│   │
│   ├── llm/                      # Utilitaires LLM
│   │   ├── queue.py              # File d'attente priorisée
│   │   └── json_utils.py         # Extraction JSON
│   │
│   ├── events/                   # Audit trail
│   │   └── event_log.py          # SQLite event log
│   │
│   ├── config.py                 # Configuration
│   └── main.py                   # Entry point FastAPI
│
├── tests/                        # Tests
│   ├── conftest.py              # Fixtures
│   └── test_*.py                # Tests par module
│
├── data/                         # Runtime data (non versionné)
│   ├── personas.db              # Base personas
│   ├── events.db                # Base événements
│   └── settings.json            # Configuration
│
├── docs/                         # Documentation
│   ├── ARCHITECTURE.md
│   ├── SPECS.md
│   ├── ROADMAP.md
│   └── BEST_PRACTICES.md
│
├── pyproject.toml               # Configuration projet
├── .pre-commit-config.yaml      # Hooks pre-commit
├── CLAUDE.md                    # Guide Claude Code
└── README.md                    # Overview projet
```

**Règles** :
- Organiser par domaine métier, pas par type technique
- `vote/`, `personas/`, `profiles/` contiennent la logique métier
- `api/routes/` est une couche mince qui délègue aux services
- Frontend vanilla JS sans framework (SPA simple)
- Un seul port exposé (:8000), FastAPI sert la SPA + l'API

---

## 2. Configuration Centralisée

### pyproject.toml

```toml
[project]
name = "voxpopulai"
version = "0.1.0"
description = "Synthetic population voting simulator powered by LLMs"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "ollama>=0.4",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "ruff>=0.8",
    "pre-commit>=4.0",
]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "SIM"]
ignore = [
    "E501",  # Line too long - handled by formatter
    "B008",  # Do not perform function calls in argument defaults (FastAPI Depends)
]

[tool.ruff.lint.isort]
known-first-party = ["app"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = ["-v", "--tb=short"]

[tool.coverage.run]
source = ["app"]
branch = true

[tool.coverage.report]
fail_under = 80
```

---

## 3. Pre-commit Hooks

### .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: ["--fix", "--exit-non-zero-on-fix"]
      - id: ruff-format
```

**Installation** :
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

---

## 4. Types et Validation

### Pydantic Models

Toutes les entrées/sorties API doivent utiliser Pydantic :

```python
from pydantic import BaseModel, Field

class VoteRequest(BaseModel):
    profile_name: str = Field(..., description="Nom du profil population")
    question: str = Field(..., min_length=10, max_length=1000)
    count: int = Field(default=100, ge=1, le=1000)
    models: List[str] = Field(default_factory=list)

class Persona(BaseModel):
    id: str
    profile_name: str
    name: str
    attributes: Dict[str, str]
    system_prompt: str
    background: str
    model: str
```

### Type Hints

```python
# ✅ Fonctions publiques typées
def generate_persona(
    profile: Profile,
    attributes: Dict[str, str],
    model: str = "qwen3:14b"
) -> Persona:
    ...

# ✅ Retours Optionnels
def get_persona(persona_id: str) -> Optional[Persona]:
    ...

# ✅ Génériques
from typing import List, Dict, Optional
```

---

## 5. Tests

### Structure

```
tests/
├── conftest.py               # Fixtures partagées
├── test_vote.py             # Tests vote
├── test_personas.py         # Tests personas
└── test_profiles.py         # Tests profiles
```

### Fixtures

```python
# conftest.py
import pytest
from app.profiles.registry import ProfileRegistry

@pytest.fixture
def sample_profile():
    return {
        "name": "test",
        "description": "Test profile",
        "attributes": {
            "sexe": {
                "values": {
                    "F": {"weight": 50},
                    "M": {"weight": 50}
                }
            }
        }
    }

@pytest.fixture
def persona_store(tmp_path):
    from app.personas.store import PersonaStore
    db_path = tmp_path / "test_personas.db"
    return PersonaStore(str(db_path))
```

### Async Testing

```python
import pytest

@pytest.mark.asyncio
async def test_vote_generation(persona_store):
    result = await synthetic_population_vote(
        profile_name="test",
        question="Test question?",
        count=5,
        store=persona_store
    )
    assert result.persona_count == 5
    assert result.tally.oui + result.tally.non + result.tally.abstention == 5
```

### Couverture

```bash
pytest tests/ --cov=app --cov-fail-under=80
```

---

## 6. Database

### SQLite Patterns

```python
# ✅ Requêtes paramétrées UNIQUEMENT
# JAMAIS de string interpolation ou concatenation

# ❌ DANGEREUX - NEVER DO THIS
cursor.execute(f"SELECT * FROM personas WHERE id = '{persona_id}'")

# ✅ CORRECT
cursor.execute("SELECT * FROM personas WHERE id = ?", (persona_id,))

# ✅ Context managers pour les connexions
from contextlib import contextmanager

@contextmanager
def get_db_connection(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
```

---

## 7. LLM Integration

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(LLMError)
)
async def generate_with_llm(prompt: str) -> str:
    return await llm_queue.submit(prompt, priority=Priority.HIGH)
```

### JSON Extraction

```python
from app.llm.json_utils import extract_json

# Le LLM peut renvoyer du markdown, des thinking blocks, etc.
raw_response = await llm_queue.submit(prompt)
parsed = extract_json(raw_response)  # Gère les cas d'erreur courants
```

### Queue Priorities

```python
from app.llm.queue import Priority

# HIGH : Opérations utilisateur (vote streaming)
# MEDIUM : Tâches de fond (analyse)
# LOW : Génération bulk personas

await llm_queue.submit(prompt, priority=Priority.HIGH, model="qwen3:14b")
```

---

## 8. Git Workflow

### Branch naming

```
<issue_id>-<short-description>

Exemples :
42-add-async-vote
67-fix-persona-generation-timeout
123-docs-update-api-specs
```

### Commits conventionnels

```bash
feat(vote): add async voting endpoint
fix(personas): handle json parsing errors
docs(api): update endpoint documentation
refactor(llm): extract json utilities
test(vote): add edge case tests
chore(deps): update ruff to 0.8.0
```

### Workflow

1. Créer une issue GitHub
2. Créer une branche : `git checkout -b <issue>-<description>`
3. Développer avec pre-commit actif
4. Lancer les tests : `pytest tests/ -v`
5. Commit avec format conventionnel
6. Push et créer une PR liée à l'issue (`closes #N`)
7. Merge quand CI verte + review OK
8. Mettre à jour `ROADMAP.md`

---

## 9. Code Style

### Python

```python
# ✅ Constantes en UPPER_CASE
MAX_PERSONA_GENERATION_RETRIES = 3
DEFAULT_VOTE_COUNT = 100

# ✅ Noms explicites
persona_count = len(personas)  # Pas: pc = len(p)
is_vote_complete = all(v.position for v in votes)  # Pas: vc = all(...)

# ✅ Docstrings pour fonctions publiques
def compute_tally(votes: List[Vote]) -> VoteTally:
    """
    Calcule le décompte des votes.
    
    Args:
        votes: Liste des votes avec position
        
    Returns:
        VoteTally avec compte et pourcentages
        
    Raises:
        ValueError: Si liste vide
    """
    if not votes:
        raise ValueError("Cannot compute tally for empty list")
    # ...
```

### JavaScript (Frontend)

```javascript
// ✅ Modules avec exports explicites
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

// ✅ Event delegation pour contenu dynamique
document.addEventListener('click', (e) => {
    if (e.target.matches('.delete-persona')) {
        const personaId = e.target.dataset.id;
        handleDelete(personaId);
    }
});
```

---

## 10. Documentation

### Quand mettre à jour

| Changement | Document à mettre à jour |
|------------|-------------------------|
| Nouvel endpoint | SPECS.md, ARCHITECTURE.md |
| Nouveau profil population | SPECS.md (section profils) |
| Changement architecture | ARCHITECTURE.md, README.md |
| Changement workflow dev | BEST_PRACTICES.md |
| Feature complète | ROADMAP.md (cocher l'issue) |

### Code documentation

```python
# ✅ Commentaires pour logique complexe uniquement
# ✅ Pas de commentaires pour ce qui est évident

# ❌ Inutile
# Increment counter
i += 1

# ✅ Utile
# Retry avec backoff exponentiel pour gérer les rate limits
# tout en évitant de surcharger le GPU
```

---

## 11. Interdictions

| ❌ Interdit | ✅ Alternative |
|-------------|--------------|
| String interpolation SQL | Requêtes paramétrées avec `?` |
| Hardcoded secrets | Variables d'environnement |
| Code mort en commentaire | Supprimer, Git garde l'historique |
| `print()` pour debug | Logging structuré |
| Fonctions > 50 lignes | Refactoring en sous-fonctions |
| Imports non utilisés | `ruff --fix` |
| Tests qui appellent vraiment Ollama | Mocker `llm_queue.submit` |
| Couverture < 80% | Ajouter des tests |

---

## 12. Checklist PR

Avant de demander une review :

- [ ] Tests passent (`pytest tests/ -v`)
- [ ] Pre-commit OK (`pre-commit run --all-files`)
- [ ] Code review par soi-même (diff complet)
- [ ] PR liée à une issue GitHub (`closes #N`)
- [ ] Documentation mise à jour si nécessaire
- [ ] Pas de logique métier dans `api/routes/`
- [ ] Pas de secrets ou credentials
- [ ] Variables et fonctions bien nommées
- [ ] Pas de code commenté inutile

---

## 13. Conventions spécifiques

### Langue

- **Documentation** : Français
- **Code (variables, fonctions)** : Anglais
- **Messages utilisateur** : Français
- **Logs** : Anglais (sauf erreurs spécifiques)

### Organisation des imports

```python
# 1. Standard library
import json
from datetime import datetime
from typing import Dict, List, Optional

# 2. Third-party
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 3. First-party (app)
from app.config import settings
from app.personas.models import Persona
from app.vote.models import Vote
```

(Ruff isort gère ça automatiquement)
