# VoxPopulAI - Spécifications

## Vue d'ensemble

VoxPopulAI est un simulateur de vote par population synthétique générée par IA.

## Architecture

### Backend (Python/FastAPI)

- **API REST** : Endpoints pour gestion des personas, votes, historique
- **LLM Integration** : Génération de personas et votes via API LLM
- **Profiles** : Définitions JSON des populations avec dimensions et poids

### Frontend (Vanilla JS/CSS)

- **Router** : Navigation hash-based sans framework
- **API Client** : Fetch avec streaming pour les votes
- **UI** : CSS custom avec variables, animations subtiles

## Modèle de données

### PopulationProfile

```python
class PopulationProfile:
    name: str           # Identifiant unique
    description: str  # Description affichée
    icon: str         # Emoji représentatif (🗳️ par défaut)
    dimensions: dict  # Dimensions démographiques
    context: str      # Contexte pour le LLM
    sources: list     # Fichiers sources additionnels
```

### Exemple de profile JSON

```json
{
  "name": "developpeurs",
  "description": "Panel de developpeurs logiciels...",
  "icon": "💻",
  "context": "Industrie du developpement logiciel...",
  "dimensions": {
    "experience": ["junior", "confirme", "senior", "expert"],
    "specialite": ["frontend", "backend", "fullstack", "devops"]
  }
}
```

## API Endpoints

### Profiles

- `GET /profiles/` - Liste tous les profils
- Retourne : `{profiles: [{name, description, icon, ...}]}`

### Personas

- `GET /personas/stats` - Statistiques par profil/modèle
- `GET /personas?offset=&limit=&profile=` - Liste paginée
- `POST /personas/generate/stream` - Génération streaming
- `DELETE /personas/{profile}` - Suppression par profil

### Vote

- `POST /vote/stream` - Vote avec streaming de progression
- Events : `progress` (phase, current, total), `done`, `error`

### Historique

- `GET /history/?limit=&offset=&mode=` - Liste des sessions
- `GET /history/{collab_id}` - Détail d'une session

## UI/UX

### Palette de couleurs

**Fonds :**
- `--bg-root: #f8fafc` - Blanc cassé bleuté
- `--bg-surface: #ffffff` - Blanc pur (cartes)
- `--bg-raised: #f1f5f9` - Gris très clair

**Accents :**
- `--accent: #3b82f6` - Bleu institutionnel
- `--accent-secondary: #8b5cf6` - Violet
- `--success: #10b981` - Vert
- `--error: #ef4444` - Rouge
- `--warning: #f59e0b` - Orange

### Composants clés

#### Sélecteur de profils (Vote)

Grille de cartes cliquables avec :
- Emoji du profil (40px)
- Nom du profil
- Description courte
- Bordure colorée au hover/sélection
- Animation `translateY(-2px)` au hover

#### Résultats de vote

- **Hero verdict** : Emoji résultat (✅/❌/➖) + position + marge
- **Barres empilées** : Dégradés verts/rouges/gris avec animations
- **Arguments** : Deux colonnes avec fonds pastel vert/rouge

#### Navigation

- Sidebar avec emojis (🗳️ 👥 📜 ⚙️)
- Effet hover : `translateX(4px)`
- Active : gradient + bordure bleue

### Animations

**Transitions :** `0.3s cubic-bezier(0.4, 0, 0.2, 1)`

**Hover cards :** `translateY(-2px)` + ombre accentuée

**Hover boutons :** `scale(0.98)` au clic

**Apparition :** `fadeUp` avec translateY(12px → 0)

## Configuration

### Variables d'environnement

```bash
# LLM Configuration
VOX_LLM_PROVIDER=openrouter  # ou openai, anthropic
VOX_LLM_API_KEY=sk-...
VOX_LLM_MODELS=gpt-4o,claude-3-opus

# Application
VOX_PORT=8282
VOX_LOG_LEVEL=info
```

### Profiles disponibles

| Profile | Emoji | Description |
|---------|-------|-------------|
| developpeurs | 💻 | Développeurs logiciels |
| donjon_et_dragon | 🗡️ | Aventuriers D&D |
| experts | 🎓 | Experts pluridisciplinaires |
| grand_public_france | 🏛️ | Population française |

## Développement

### Installation

```bash
pip install -e .
```

### Lancer l'application

```bash
python -m app.main
```

### Frontend

Les fichiers statiques sont servis depuis `app/frontend/` :
- `index.html` - Structure de base
- `css/style.css` - Styles
- `js/app.js` - Point d'entrée
- `js/views/*.js` - Vues (vote, personas, history, settings)

### Tests

```bash
pytest tests/
```

## Roadmap

Voir `docs/ROADMAP.md` pour les fonctionnalités planifiées.
