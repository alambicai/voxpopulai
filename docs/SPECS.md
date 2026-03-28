# Specifications

## API Endpoints

### Vote Endpoints (`/api/vote`)

#### POST `/api/vote/`
Run a synchronous synthetic population vote.

**Request Body:**
```json
{
  "profile_name": "grand_public_france",
  "question": "Faut-il interdire les smartphones dans les écoles ?",
  "count": 100,
  "models": ["qwen3:14b"]
}
```

**Response:**
```json
{
  "profile_name": "grand_public_france",
  "question": "Faut-il interdire les smartphones dans les écoles ?",
  "persona_count": 100,
  "tally": {
    "oui": 67,
    "non": 23,
    "abstention": 10,
    "oui_pct": 67.0,
    "non_pct": 23.0,
    "abstention_pct": 10.0
  },
  "analysis": {
    "dominant_position": "oui",
    "margin": 44.0,
    "key_arguments": {
      "oui": ["Distraction en classe", "Addiction aux écrans"],
      "non": ["Outil pédagogique", "Communication parents-enfants"]
    },
    "demographic_patterns": [
      "Les parents d'enfants en bas âge sont plus favorables",
      "Les 18-24 ans s'opposent majoritairement"
    ],
    "consensus_level": "modere"
  },
  "disclaimer": "Cette simulation est générée par IA et ne reflète pas nécessairement l'opinion réelle de la population.",
  "collaboration_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses:**
- `400`: Invalid profile name or parameters
- `422`: Validation error (missing required fields)
- `500`: Internal server error during vote processing

#### POST `/api/vote/stream`
Run a vote with Server-Sent Events streaming for real-time progress updates.

**Request Body:** Same as `/api/vote/`

**Response:** SSE stream with event types:
- `progress`: `{ "type": "progress", "current": 5, "total": 100, "percentage": 5.0 }`
- `persona_vote`: `{ "type": "persona_vote", "persona_id": "...", "position": "oui", "reasoning": "..." }`
- `complete`: Final result object (same as `/api/vote/` response)
- `error`: `{ "type": "error", "message": "..." }`

#### POST `/api/vote/async`
Start an asynchronous vote that runs in the background.

**Request Body:** Same as `/api/vote/`

**Response:**
```json
{
  "collaboration_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending"
}
```

#### GET `/api/vote/{collaboration_id}/status`
Get the status of an asynchronous vote.

**Response:**
```json
{
  "collaboration_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": {
    "current": 100,
    "total": 100,
    "percentage": 100.0
  },
  "result": { ... }  // Complete result if finished
}
```

Status values: `pending`, `running`, `completed`, `failed`

---

### Personas Endpoints (`/api/personas`)

#### GET `/api/personas/`
List stored personas with pagination.

**Query Parameters:**
- `profile` (optional): Filter by profile name
- `limit` (default: 50): Number of results
- `offset` (default: 0): Pagination offset

**Response:**
```json
{
  "personas": [
    {
      "id": "uuid",
      "profile_name": "grand_public_france",
      "name": "Marie Dubois",
      "attributes": {
        "sexe": "F",
        "age": "45-54",
        "csp": "Cadre",
        "habitat": "urbain"
      },
      "model": "qwen3:14b",
      "created_at": "2024-03-27T10:30:00Z"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

#### POST `/api/personas/generate`
Generate new personas for a profile.

**Request Body:**
```json
{
  "profile_name": "grand_public_france",
  "count": 50,
  "generation_model": "qwen3:14b",
  "generation_temperature": 0.8
}
```

**Response:**
```json
{
  "generated": 50,
  "personas": [ ... ]  // Array of generated persona objects
}
```

#### POST `/api/personas/generate/stream`
Generate personas with SSE streaming progress.

**Request Body:** Same as `/api/personas/generate`

**SSE Events:**
- `persona_generated`: Individual persona as generated
- `progress`: Generation progress
- `complete`: Final summary
- `error`: Error information

#### GET `/api/personas/stats`
Get global statistics about stored personas.

**Response:**
```json
{
  "total_personas": 500,
  "by_profile": {
    "grand_public_france": 300,
    "experts": 100,
    "developpeurs": 100
  },
  "by_model": {
    "qwen3:14b": 400,
    "llama3:8b": 100
  }
}
```

#### GET `/api/personas/distribution/{profile_name}`
Get attribute distribution for a profile.

**Response:**
```json
{
  "profile_name": "grand_public_france",
  "distributions": {
    "sexe": {
      "F": 52,
      "M": 48
    },
    "age": {
      "18-24": 12,
      "25-34": 18,
      "35-49": 25,
      "50-64": 28,
      "65+": 17
    },
    "csp": {
      "Agriculteur": 2,
      "Artisan": 6,
      "Cadre": 15,
      "Profession intermédiaire": 24,
      "Employé": 28,
      "Ouvrier": 15,
      "Retraité": 10
    }
  }
}
```

#### GET `/api/personas/{profile_name}/models`
Get models used for a specific profile.

**Response:**
```json
{
  "profile_name": "grand_public_france",
  "models": ["qwen3:14b", "llama3:8b"]
}
```

#### DELETE `/api/personas/{profile_name}`
Delete all personas for a profile.

**Response:** `204 No Content`

#### DELETE `/api/personas/{profile_name}/model/{model}`
Delete personas for a profile generated with a specific model.

**Response:** `204 No Content`

#### DELETE `/api/personas/{profile_name}/attribute`
Delete personas matching specific attributes.

**Request Body:**
```json
{
  "attributes": {
    "sexe": "F",
    "age": "18-24"
  }
}
```

**Response:** `204 No Content`

---

### Profiles Endpoints (`/api/profiles`)

#### GET `/api/profiles/`
List all available population profiles.

**Response:**
```json
{
  "profiles": [
    {
      "name": "grand_public_france",
      "description": "Population française adulte représentative (2024)",
      "attribute_count": 9,
      "total_weight": 100
    },
    {
      "name": "experts",
      "description": "Panel multidisciplinaire d'experts",
      "attribute_count": 5,
      "total_weight": 50
    },
    {
      "name": "developpeurs",
      "description": "Développeurs logiciels",
      "attribute_count": 4,
      "total_weight": 30
    },
    {
      "name": "donjon_et_dragon",
      "description": "Groupe d'aventuriers D&D 5e",
      "attribute_count": 6,
      "total_weight": 5
    }
  ]
}
```

---

### History Endpoints (`/api/history`)

#### GET `/api/history/`
List voting sessions with pagination.

**Query Parameters:**
- `limit` (default: 20): Number of results
- `offset` (default: 0): Pagination offset

**Response:**
```json
{
  "sessions": [
    {
      "collaboration_id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2024-03-27T10:30:00Z",
      "profile_name": "grand_public_france",
      "question": "Faut-il interdire les smartphones dans les écoles ?",
      "persona_count": 100,
      "tally": {
        "oui": 67,
        "non": 23,
        "abstention": 10
      }
    }
  ],
  "total": 50,
  "limit": 20,
  "offset": 0
}
```

#### GET `/api/history/{collaboration_id}`
Reconstruct a complete voting session.

**Response:**
```json
{
  "collaboration_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-03-27T10:30:00Z",
  "profile_name": "grand_public_france",
  "question": "Faut-il interdire les smartphones dans les écoles ?",
  "votes": [
    {
      "persona": { ... },
      "position": "oui",
      "reasoning": "Les smartphones sont une source de distraction..."
    }
  ],
  "tally": { ... },
  "analysis": { ... }
}
```

#### GET `/api/history/{collaboration_id}/audit`
Get cross-tabulation audit for demographic analysis.

**Response:**
```json
{
  "collaboration_id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "Faut-il interdire les smartphones dans les écoles ?",
  "crosstabs": {
    "sexe": {
      "F": { "oui": 35, "non": 12, "abstention": 5 },
      "M": { "oui": 32, "non": 11, "abstention": 5 }
    },
    "age": {
      "18-24": { "oui": 5, "non": 6, "abstention": 1 },
      "25-34": { "oui": 10, "non": 6, "abstention": 2 }
    }
  },
  "metadata": {
    "total_votes": 100,
    "attribute_coverage": {
      "sexe": 100,
      "age": 98,
      "csp": 95
    }
  }
}
```

---

### Settings Endpoints (`/api/settings`)

#### GET `/api/settings/`
Get current application settings.

**Response:**
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
    "num_predict": -1,
    "top_k": 40,
    "top_p": 0.9,
    "temperature": 0.8
  }
}
```

#### PUT `/api/settings/synthetic`
Update synthetic vote settings.

**Request Body:** Partial or complete SyntheticSettings object

**Response:** Updated settings object

#### PUT `/api/settings/ollama`
Update Ollama runtime settings.

**Request Body:** Partial or complete OllamaSettings object

**Response:** Updated settings object

---

### Models Endpoints (`/api/models`)

#### GET `/api/models/`
List available Ollama models.

**Response:**
```json
{
  "models": [
    {
      "name": "qwen3:14b",
      "size": "8.9GB",
      "parameter_size": "14B",
      "quantization": "Q4_K_M"
    },
    {
      "name": "llama3:8b",
      "size": "4.7GB",
      "parameter_size": "8B",
      "quantization": "Q4_K_M"
    }
  ]
}
```

---

## Data Models

### Persona

```python
class Persona(BaseModel):
    id: str                          # UUID v4
    name: str                       # Generated full name
    attributes: Dict[str, str]       # Demographic attributes from profile
    system_prompt: str               # LLM system prompt for the persona
    background: str                  # Rich backstory (2-3 paragraphs)
    model: str                       # LLM used for generation
```

**Example:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Marie Dubois",
  "attributes": {
    "sexe": "F",
    "age": "45-54",
    "csp": "Cadre",
    "habitat": "urbain",
    "education": "Bac+5",
    "situation_familiale": "Marié(e)",
    "nb_enfants": "2",
    "sensibilite_politique": "Centre",
    "religion": "Catholique non pratiquant"
  },
  "system_prompt": "Tu es Marie Dubois, 48 ans, cadre dans une grande entreprise...",
  "background": "Marie Dubois a grandi en banlieue parisienne... Elle est mariée depuis 15 ans...",
  "model": "qwen3:14b"
}
```

### Vote

```python
class Vote(BaseModel):
    persona: Persona                 # The voting persona
    position: Literal["oui", "non", "abstention"]
    reasoning: str                   # Free-text opinion and justification
```

### VoteTally

```python
class VoteTally(BaseModel):
    oui: int                         # Count of "oui" votes
    non: int                         # Count of "non" votes
    abstention: int                  # Count of "abstention" votes
    oui_pct: float                   # Percentage (0-100)
    non_pct: float                   # Percentage (0-100)
    abstention_pct: float             # Percentage (0-100)
```

### VoteAnalysis

```python
class VoteAnalysis(BaseModel):
    dominant_position: Literal["oui", "non", "abstention", "indecis"]
    margin: float                     # Difference between 1st and 2nd position
    key_arguments: Dict[str, List[str]]  # {"oui": [...], "non": [...]}
    demographic_patterns: List[str]   # Insights about voting patterns
    consensus_level: Literal["fort", "modere", "faible", "aucun"]
```

### SyntheticVoteResult

```python
class SyntheticVoteResult(BaseModel):
    profile_name: str
    question: str
    persona_count: int
    tally: VoteTally
    analysis: VoteAnalysis
    disclaimer: str                   # Fixed disclaimer text
    collaboration_id: Optional[str]   # UUID for audit trail
```

### VoteRequest

```python
class VoteRequest(BaseModel):
    profile_name: str                 # Must match available profile
    question: str                     # The question to vote on
    count: int = Field(default=100, ge=1, le=1000)  # Number of personas
    models: List[str] = []            # LLM models to use (default from settings)
```

### Profile

Population profiles are defined in JSON files with this structure:

```json
{
  "name": "grand_public_france",
  "description": "Population française adulte représentative (2024)",
  "attributes": {
    "sexe": {
      "values": {
        "F": {"weight": 52, "description": "Femme"},
        "M": {"weight": 48, "description": "Homme"}
      }
    },
    "age": {
      "values": {
        "18-24": {"weight": 12, "description": "18 à 24 ans"},
        "25-34": {"weight": 18, "description": "25 à 34 ans"},
        "35-49": {"weight": 25, "description": "35 à 49 ans"},
        "50-64": {"weight": 28, "description": "50 à 64 ans"},
        "65+": {"weight": 17, "description": "65 ans et plus"}
      }
    }
  }
}
```

### Settings Models

#### SyntheticSettings

```python
class SyntheticSettings(BaseModel):
    generation_model: str = "qwen3:14b"           # LLM for persona generation
    generation_temperature: float = 0.8            # Creativity (0.0 - 2.0)
    judge_model: str = ""                          # LLM for quality validation (optional)
    judge_temperature: float = 0.1                 # Low for consistency
    judge_max_retries: int = 2                     # Max validation retries
    persona_models: List[str] = ["qwen3:14b"]      # LLMs for voting
    analysis_model: str = "qwen3:14b"             # LLM for result analysis
```

#### OllamaSettings

```python
class OllamaSettings(BaseModel):
    num_ctx: int = 8192           # Context window size
    num_predict: int = -1         # Max tokens to predict (-1 = unlimited)
    top_k: int = 40               # Top-k sampling
    top_p: float = 0.9            # Nucleus sampling
    temperature: float = 0.8      # Sampling temperature
    repeat_penalty: float = 1.1   # Repetition penalty
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
```

---

## Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DATA_DIR` | `./data` | No | Runtime data directory path |
| `PERSONA_DB_PATH` | `./data/personas.db` | No | Path to personas SQLite database |
| `EVENTS_DB_PATH` | `./data/events.db` | No | Path to events SQLite database |
| `SETTINGS_PATH` | `./data/settings.json` | No | Path to settings JSON file |
| `OLLAMA_HOST` | `http://localhost:11434` | No | Ollama API base URL |

---

## Built-in Profiles

### grand_public_france

**Description:** Population française adulte représentative (2024)

**Source:** INSEE data

**Attributes:**
- `sexe`: F (52%), M (48%)
- `age`: 18-24 (12%), 25-34 (18%), 35-49 (25%), 50-64 (28%), 65+ (17%)
- `csp`: Agriculture (2%), Artisan (6%), Cadre (15%), Profession intermédiaire (24%), Employé (28%), Ouvrier (15%), Retraité (10%)
- `habitat`: Urbain (75%), Periurbain (15%), Rural (10%)
- `education`: Sans diplôme (8%), CAP/BEP (16%), Bac (22%), Bac+2 (20%), Bac+3/4 (18%), Bac+5+ (16%)
- `situation_familiale`: Célibataire (35%), Marié(e) (45%), Divorcé(e) (10%), Veuf/Veuve (5%), Pacsé(e) (5%)
- `nb_enfants`: 0 (40%), 1 (20%), 2 (25%), 3+ (15%)
- `sensibilite_politique`: Extrême gauche (5%), Gauche (20%), Centre (25%), Droite (25%), Extrême droite (15%), Sans opinion (10%)
- `religion`: Catholique pratiquant (8%), Catholique non pratiquant (35%), Athée/Agnostique (35%), Musulman (8%), Autre (14%)

### experts

**Description:** Panel multidisciplinaire d'experts

**Attributes:**
- `expertise_domain`: Tech (25%), Science (20%), Économie (20%), Droit (15%), Santé (20%)
- `seniority`: Junior (30%), Senior (50%), Expert (20%)
- `institution_type`: Université (30%), Entreprise (40%), Institution publique (20%), Indépendant (10%)
- `geography`: Europe (50%), Amérique du Nord (25%), Asie (15%), Autre (10%)
- `publication_record`: Aucune (20%), Modérée (50%), Importante (30%)

### developpeurs

**Description:** Développeurs logiciels

**Attributes:**
- `experience_level`: Junior (35%), Senior (40%), Lead (20%), Architect (5%)
- `primary_language`: Python (30%), JavaScript (25%), Java (15%), Go (10%), Rust (8%), Autre (12%)
- `company_type`: Startup (35%), Enterprise (40%), Agency (15%), Freelance (10%)
- `remote_work`: 100% remote (30%), Hybride (50%), Sur site (20%)

### donjon_et_dragon

**Description:** Groupe d'aventuriers Donjons & Dragons 5e

**Attributes:**
- `race`: Humain (35%), Elfe (20%), Nain (15%), Halfelin (10%), Demi-elfe (10%), Demi-orque (5%), Gnome (5%)
- `classe`: Guerrier (20%), Magicien (15%), Voleur (15%), Clerc (15%), Rôdeur (10%), Barde (10%), Barbare (8%), Paladin (7%)
- `niveau`: 1-3 (30%), 4-6 (40%), 7-10 (20%), 11-15 (8%), 16-20 (2%)
- `background`: Soldat (20%), Erudit (15%), Criminel (12%), Acolyte (12%), Artiste (10%), Autre (31%)
- `alignement`: Loyal Bon (15%), Neutre Bon (20%), Chaotique Bon (15%), Loyal Neutre (10%), Neutre (15%), Chaotique Neutre (10%), Loyal Mauvais (5%), Neutre Mauvais (5%), Chaotique Mauvais (5%)
- `setting`: Faerûn (70%), Eberron (15%), Greyhawk (10%), Autre (5%)

---

## Error Handling

### HTTP Status Codes

- `200 OK`: Successful GET/PUT operations
- `201 Created`: Successful POST operations (where applicable)
- `204 No Content`: Successful DELETE operations
- `400 Bad Request`: Invalid parameters or request body
- `404 Not Found`: Resource does not exist
- `422 Unprocessable Entity`: Validation error (Pydantic)
- `500 Internal Server Error`: Server-side error

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

For validation errors:
```json
{
  "detail": [
    {
      "loc": ["body", "count"],
      "msg": "ensure this value is less than or equal to 1000",
      "type": "value_error.number.not_le"
    }
  ]
}
```

---

## Rate Limiting

No built-in rate limiting is currently implemented. For production deployment, consider:

- Nginx rate limiting
- FastAPI middleware for rate limiting
- Ollama queue depth monitoring

---

## Pagination

All list endpoints use offset-based pagination:

**Query Parameters:**
- `limit`: Maximum items to return (default varies by endpoint)
- `offset`: Number of items to skip (default: 0)

**Response includes:**
- `total`: Total number of items available
- `limit`: Limit applied to this request
- `offset`: Offset applied to this request

**Example navigation:**
```
GET /api/personas/?limit=50&offset=0    # First page
GET /api/personas/?limit=50&offset=50   # Second page
GET /api/personas/?limit=50&offset=100  # Third page
```
