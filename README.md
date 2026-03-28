# VoxPopulAI - Simulateur de Vote par Population Synthétique

## Objectif

VoxPopulAI est un **laboratoire d'exploration des LLMs** (Large Language Models) via la simulation de votes. Il génère des **personas fictifs** avec des profils sociodémographiques variés qui votent indépendamment sur des questions, permettant d'observer comment les modèles de langage réagissent différemment selon le contexte et les attributs attribués.

**Ce que ça explore :**
- **Comportement des LLMs** - Comment un même modèle produit des réponses différentes selon le persona qui "vote"
- **Limites des modèles** - Jusqu'où les biais et patterns de génération influencent les résultats
- **Impact du contexte** - Comment un changement de profil (âge, CSP, région...) modifie la "position" générée
- **Variations de raisonnement** - Les arguments produits sont-ils cohérents avec le persona ou des clichés de l'entraînement ?

**Ce que ça ne fait PAS :**
- Prédire l'opinion réelle d'une population
- Remplacer des études sociologiques ou des sondages
- Simuler fidèlement la réalité sociodémographique

Les résultats sont des **artefacts de génération LLM** à interpréter comme tels, pas comme des données empiriques.

---

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│  SPA vanilla JS (servi par FastAPI :8000)                   │
│  ├── Vote (création + résultats en temps réel)              │
│  ├── Personas (génération, stats, distributions)          │
│  ├── History (historique des sessions + audit)              │
│  └── Settings (configuration des modèles LLM)               │
└─────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│  Services Layer (logique métier)                            │
│  ├── vote/orchestrator.py    Orchestration complète du vote │
│  ├── personas/generator.py   Génération LLM des personas    │
│  ├── personas/store.py       Persistance SQLite              │
│  ├── personas/name_generators.py  Noms réalistes (INSEE)     │
│  ├── profiles/registry.py    Gestion des profils population  │
│  ├── llm/queue.py           File d'attente priorisée Ollama │
│  ├── llm/json_utils.py       Extraction JSON des réponses   │
│  └── events/event_log.py     Audit des sessions              │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   SQLite     │    │    Ollama    │    │   Settings │
│  personas.db │    │   (:11434)   │    │  settings.json│
│  events.db   │    │              │    │             │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## Prérequis

- **Python** 3.10+
- **Ollama** installé et accessible (`http://localhost:11434`)
- Modèles Ollama recommandés :

```bash
# Modèle principal (chat + génération personas + analyse)
ollama pull qwen3:14b

# Alternative plus légère
ollama pull llama3:8b
```

---

## Quick Start

```bash
# Cloner et configurer
git clone <repo-url>
cd voxpopulai
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Vérifier Ollama
ollama list

# Lancer l'application
python -m app.main

# Accéder à l'application
# http://localhost:8000
```

---

## Fonctionnement

### 1. Génération des Personas

Les personas sont générés à partir d'un **profil de population** (ex: `grand_public_france`) :
- Attributs sociodémographiques échantillonnés selon les poids du profil (âge, CSP, région...)
- Nom généré selon les statistiques INSEE (prénoms et patronymes réalistes)
- Background et personnalité créés par LLM
- Persistés en SQLite pour réutilisation

### 2. Vote

Chaque persona vote indépendamment :
- **Position** : OUI / NON / ABSTENTION
- **Raisonnement** : Opinion détaillée en français
- **Confiance** : Niveau de certitude (optionnel)

### 3. Analyse

Un LLM analyse l'ensemble des votes pour produire :
- **Résultat quantitatif** : Décompte et pourcentages
- **Position dominante** : Oui/Non/Abstention/Indécis avec marge
- **Arguments clés** : Points principaux des partisans et opposants
- **Patterns démographiques** : Corrélations attributs ↔ votes
- **Niveau de consensus** : Fort / Modéré / Faible / Aucun

### Progression en temps réel

Les endpoints SSE (`/api/vote/stream`, `/api/personas/generate/stream`) envoient des événements de progression à chaque étape. Le frontend affiche :
- Barre de progression déterministe (ex: "Personas 45/100")
- Votes en cours d'arrivée
- Phase d'analyse finale

---

## Profils de population

| Profil | Description | Contexte |
|--------|-------------|----------|
| **grand_public_france** | Population française adulte représentative | France 2024, données INSEE |
| **experts** | Panel multidisciplinaire d'experts | Contexte professionnel |
| **developpeurs** | Développeurs logiciels | Tech industry |
| **donjon_et_dragon** | Groupe d'aventuriers D&D 5e | Forgotten Realms |

Chaque profil définit des dimensions pondérées (âge, CSP, région, religion, etc.) dans des fichiers JSON dans `app/profiles/definitions/`.

---

## API Endpoints principaux

| Endpoint | Description |
|----------|-------------|
| `POST /api/vote/` | Vote synchrone |
| `POST /api/vote/stream` | Vote avec streaming SSE |
| `POST /api/vote/async` | Vote asynchrone (background) |
| `GET /api/vote/{id}/status` | Statut vote async |
| `POST /api/personas/generate` | Génération personas |
| `POST /api/personas/generate/stream` | Génération avec SSE |
| `GET /api/personas/stats` | Statistiques globales |
| `GET /api/history/` | Historique des sessions |
| `GET /api/history/{id}/audit` | Audit cross-tab par attribut |
| `GET /api/profiles/` | Liste des profils disponibles |
| `GET /api/settings/` | Configuration actuelle |

Voir [SPECS.md](SPECS.md) pour la documentation complète de l'API.

---

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture technique détaillée
- [SPECS.md](SPECS.md) - Spécifications fonctionnelles et API
- [ROADMAP.md](ROADMAP.md) - Roadmap du projet
- [BEST_PRACTICES.md](BEST_PRACTICES.md) - Standards de développement
- [CLAUDE.md](CLAUDE.md) - Guide pour Claude Code

---

## Tests

```bash
# Tous les tests
pytest tests/ -v

# Tests spécifiques
pytest tests/test_vote.py -v

# Avec couverture
pytest tests/ --cov=app --cov-fail-under=80
```

---

## Stack technique

- **Backend** : Python 3.10+, FastAPI, Pydantic
- **Frontend** : SPA vanilla JS (hash routing)
- **LLM** : Ollama (local)
- **Base de données** : SQLite (personas, events)
- **Configuration** : JSON settings file
- **Linting** : Ruff

---

## Disclaimer

VoxPopulAI explore **le comportement des modèles de langage**, pas la réalité sociologique. Les votes générés reflètent les patterns, biais et limitations de l'entraînement des LLMs utilisés.

- Pas de prétention de validité empirique ou sociologique
- Les corrélations observées sont des artefacts de génération, pas des découvertes démographiques
- À utiliser comme outil d'expérimentation sur les LLMs, pas comme base décisionnelle

Pour des études d'opinion réelles, utilisez des méthodologies éprouvées et des échantillons représentatifs.

---

## License

MIT
