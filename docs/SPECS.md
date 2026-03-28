# VoxPopulAI - Spécifications

> Simulateur de vote par population synthétique propulsé par LLM.

---

## Pourquoi VoxPopulAI

VoxPopulAI permet d'**explorer les opinions** d'une population simulée avant de prendre des décisions importantes, de valider des intuitions sur les tendances démographiques, ou simplement de comprendre comment différents profils perçoivent un sujet.

### Cas d'usage

| Besoin | Comment |
| ------ | ------- |
| **Sondage avant référendum** | Simuler 1000 citoyens sur une question de société |
| **Validation produit** | Tester la réaction de développeurs à une nouvelle feature |
| **Worldbuilding** | Simuler un vote dans l'univers D&D (quartier des nains vs elfes) |
| **Éducation** | Comprendre les clivages sociétaux sur des sujets historiques |
| **Veille** | Explorer les opinions de différentes populations sur un sujet émergent |

### Bénéfices

- **Rapide** : Obtenir des insights en minutes, pas en semaines de sondage
- **Contrôlé** : Tester différentes populations (âge, CSP, région) indépendamment
- **Explicatif** : Chaque vote inclut un raisonnement, pas juste un chiffre
- **Audit** : Traçabilité complète des décisions de chaque persona
- **Local** : Pas de données externes, tout tourne sur votre machine

---

## Scénarios illustrés

### Scénario 1 — "Référendum sur les smartphones à l'école"

```
Toi : "Faut-il interdire les smartphones dans les écoles ?"

→ Profil : grand_public_france
→ Nombre de personas : 500
→ Question : "Faut-il interdire les smartphones dans les écoles ?"

VoxPopulAI :
  Phase 1 — Génération : 500 personas avec attributs réalistes
  Phase 2 — Vote : chaque persona vote avec son contexte propre
  
  Exemples de votes :
  
  Marie Dubois (45 ans, cadre, 2 enfants) :
    Position : OUI
    Raisonnement : "En tant que mère, je vois l'addiction aux écrans.
                    Mes enfants sont déjà trop connectés."
  
  Lucas Martin (22 ans, étudiant) :
    Position : NON  
    Raisonnement : "C'est un outil pédagogique. Les interdire c'est
                    nier l'évolution technologique."
  
  Résultat :
    OUI : 67% (335 votes)
    NON : 23% (115 votes)
    ABSTENTION : 10% (50 votes)
  
  Analyse qualitative :
    Position dominante : OUI (marge +44%)
    Arguments OUI : "Addiction", "Distraction", "Violence scolaire"
    Arguments NON : "Outil pédagogique", "Digital native", "Urgences"
    Patterns : Les parents d'enfants favorables +66%, 18-24 ans opposés

Résultat : une vision nuancée avec arguments des deux côtés.
```

### Scénario 2 — "Validation d'une feature tech"

```
Toi : "Est-ce que les développeurs accepteraient un déploiement
        automatique sans review ?"

→ Profil : developpeurs
→ Nombre : 100
→ Question : "Êtes-vous favorable au déploiement automatique sans
              review humaine pour les hotfixes critiques ?"

VoxPopulAI :
  Phase 1 — Génération : 100 devs avec niveaux d'expérience variés
  Phase 2 — Vote : consultation des personas
  
  Exemples :
  
  Senior DevOps (12 ans exp) :
    Position : OUI (avec conditions)
    Raisonnement : "Si tests auto complets + rollback instantané,
                    c'est plus sûr qu'un humain pressé à 3h du mat."
  
  Junior Frontend (2 ans exp) :
    Position : NON
    Raisonnement : "Trop risqué. J'ai déjà cassé la prod en pensant
                    que mon fix était simple. Review obligatoire."
  
  Lead Architect (15 ans exp) :
    Position : ABSTENTION
    Raisonnement : "Dépend du contexte. Hotfix oui, feature non.
                    Trop nuancé pour une réponse binaire."

  Résultat :
    OUI : 35% (mais majoritairement "avec conditions")
    NON : 45%
    ABSTENTION : 20%
  
  Patterns démographiques :
    - Seniorité inversement corrélée avec opposition
    - DevOps plus favorables que développeurs frontend
    - Ceux qui ont connu des outages majeurs opposés

Résultat : le consensus n'existe pas, implémentation risquée.
```

### Scénario 3 — "Vote dans l'univers D&D"

```
Toi : "Le conseil des guildes doit-il autoriser la magie nécromancienne
        dans la ville de Waterdeep ?"

→ Profil : donjon_et_dragon
→ Nombre : 50
→ Contexte : Faerûn, D&D 5e

VoxPopulAI génère 50 aventuriers :
- 5 paladins (Loyal Bon) → majoritairement CONTRE
- 8 magiciens (dont 2 nécromanciens) → majoritairement POUR  
- 3 clercs de Kelemvor → FERMEMENT CONTRE
- 6 roublards → majoritairement ABSTENTION (pas leur problème)
- etc.

Résultat :
  OUI : 30% (magiciens, certains warlocks)
  NON : 55% (paladins, clercs, rôdeurs)
  ABSTENTION : 15% (roublards, barbares)

Analyse :
  Position dominante : NON (marge 25%)
  Argument clé OUI : "Contrôler la mort ≠ la malédiction"
  Argument clé NON : "Ouvrir la porte au culte du serpent"
  Pattern : Alignement détermine 80% des votes

Usage : scénario de campagne avec tensions politiques réalistes.
```

---

## API Endpoints

### Vote

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/vote/` | POST | Vote synchrone (blocking) |
| `/api/vote/stream` | POST | Vote avec streaming SSE |
| `/api/vote/async` | POST | Vote asynchrone (background) |
| `/api/vote/{id}/status` | GET | Statut vote async |

**POST /api/vote/** — Request:
```json
{
  "profile_name": "grand_public_france",
  "question": "Faut-il interdire les smartphones dans les écoles ?",
  "count": 100,
  "models": ["qwen3:14b"]
}
```

**POST /api/vote/** — Response:
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
  "disclaimer": "Cette simulation est générée par IA...",
  "collaboration_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**SSE Events** (streaming):
- `{"type": "progress", "phase": "personas", "current": 45, "total": 100}`
- `{"type": "progress", "phase": "votes", "current": 67, "total": 100}`
- `{"type": "vote", "persona_id": "...", "position": "oui", "reasoning": "..."}`
- `{"type": "complete", "result": {...}}`

---

### Personas

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/personas/` | GET | Liste personas (paginé) |
| `/api/personas/generate` | POST | Génération batch |
| `/api/personas/generate/stream` | POST | Génération SSE |
| `/api/personas/stats` | GET | Stats globales |
| `/api/personas/distribution/{profile}` | GET | Distribution attributs |
| `/api/personas/{profile}` | DELETE | Suppression par profil |

**POST /api/personas/generate** — Request:
```json
{
  "profile_name": "grand_public_france",
  "count": 50,
  "generation_model": "qwen3:14b",
  "generation_temperature": 0.8
}
```

---

### History

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/history/` | GET | Liste sessions |
| `/api/history/{id}` | GET | Session complète |
| `/api/history/{id}/audit` | GET | Audit cross-tab |

**GET /api/history/{id}/audit** — Response:
```json
{
  "collaboration_id": "550e8400-...",
  "question": "Faut-il interdire...",
  "crosstabs": {
    "sexe": {
      "F": {"oui": 35, "non": 12, "abstention": 5},
      "M": {"oui": 32, "non": 11, "abstention": 5}
    },
    "age": {
      "18-24": {"oui": 5, "non": 6, "abstention": 1},
      "25-34": {"oui": 10, "non": 6, "abstention": 2}
    }
  }
}
```

---

### Profiles & Settings

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/profiles/` | GET | Liste profils disponibles |
| `/api/settings/` | GET/PUT | Configuration |
| `/api/models/` | GET | Modèles Ollama disponibles |

---

## Modèles de données

### Persona

```python
class Persona(BaseModel):
    id: str                          # UUID
    profile_name: str               # ex: "grand_public_france"
    name: str                       # "Marie Dubois"
    attributes: Dict[str, str]       # Dimensions sociodémographiques
    system_prompt: str               # Prompt système LLM
    background: str                  # Histoire et contexte
    model: str                      # LLM de génération
```

### Vote

```python
class Vote(BaseModel):
    persona: Persona
    position: Literal["oui", "non", "abstention"]
    reasoning: str                   # Raisonnement détaillé
```

### Profile

```json
{
  "name": "grand_public_france",
  "description": "Population française adulte représentative",
  "attributes": {
    "sexe": {
      "values": {
        "F": {"weight": 52, "description": "Femme"},
        "M": {"weight": 48, "description": "Homme"}
      }
    },
    "age": {
      "values": {
        "18-24": {"weight": 12},
        "25-34": {"weight": 18},
        "35-49": {"weight": 25},
        "50-64": {"weight": 28},
        "65+": {"weight": 17}
      }
    }
  }
}
```

---

## Profils de population intégrés

### grand_public_france

**Source** : Données INSEE 2024

**Dimensions** (9 attributs) :
- `sexe` : F (52%), M (48%)
- `age` : 18-24 (12%), 25-34 (18%), 35-49 (25%), 50-64 (28%), 65+ (17%)
- `csp` : Agriculture (2%), Artisan (6%), Cadre (15%), Profession intermédiaire (24%), Employé (28%), Ouvrier (15%), Retraité (10%)
- `habitat` : Urbain (75%), Periurbain (15%), Rural (10%)
- `education` : Sans diplôme (8%), CAP/BEP (16%), Bac (22%), Bac+2 (20%), Bac+3/4 (18%), Bac+5+ (16%)
- `situation_familiale` : Célibataire (35%), Marié(e) (45%), Divorcé(e) (10%), Veuf/Veuve (5%), Pacsé(e) (5%)
- `nb_enfants` : 0 (40%), 1 (20%), 2 (25%), 3+ (15%)
- `sensibilite_politique` : Extrême gauche (5%), Gauche (20%), Centre (25%), Droite (25%), Extrême droite (15%), Sans opinion (10%)
- `religion` : Catholique pratiquant (8%), Catholique non pratiquant (35%), Athée/Agnostique (35%), Musulman (8%), Autre (14%)

### experts

**Dimensions** (5 attributs) :
- `expertise_domain` : Tech, Science, Économie, Droit, Santé
- `seniority` : Junior, Senior, Expert
- `institution_type` : Université, Entreprise, Publique, Indépendant
- `geography` : Europe, Amérique du Nord, Asie, Autre
- `publication_record` : Aucune, Modérée, Importante

### developpeurs

**Dimensions** (4 attributs) :
- `experience_level` : Junior (35%), Senior (40%), Lead (20%), Architect (5%)
- `primary_language` : Python (30%), JavaScript (25%), Java (15%), Go (10%), Rust (8%), Autre (12%)
- `company_type` : Startup (35%), Enterprise (40%), Agency (15%), Freelance (10%)
- `remote_work` : 100% remote (30%), Hybride (50%), Sur site (20%)

### donjon_et_dragon

**Dimensions** (6 attributs) — D&D 5e, Forgotten Realms :
- `race` : Humain (35%), Elfe (20%), Nain (15%), Halfelin (10%), Demi-elfe (10%), Demi-orque (5%), Gnome (5%)
- `classe` : Guerrier (20%), Magicien (15%), Voleur (15%), Clerc (15%), Rôdeur (10%), Barde (10%), Barbare (8%), Paladin (7%)
- `niveau` : 1-3 (30%), 4-6 (40%), 7-10 (20%), 11-15 (8%), 16-20 (2%)
- `background` : Soldat, Erudit, Criminel, Acolyte, Artiste...
- `alignement` : Loyal Bon (15%), Neutre Bon (20%), Chaotique Bon (15%), Neutre (15%), etc.
- `setting` : Faerûn (70%), Eberron (15%), Greyhawk (10%), Autre (5%)

---

## Configuration

### Settings (data/settings.json)

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

### Variables d'environnement

| Variable | Défaut | Description |
|----------|--------|-------------|
| `DATA_DIR` | `./data` | Répertoire données runtime |
| `PERSONA_DB_PATH` | `./data/personas.db` | Base personas |
| `EVENTS_DB_PATH` | `./data/events.db` | Base événements |
| `SETTINGS_PATH` | `./data/settings.json` | Configuration |
| `OLLAMA_HOST` | `http://localhost:11434` | URL API Ollama |

---

## Limites et avertissements

### Ce que VoxPopulAI fait bien

- ✅ Explorer des tendances démographiques simulées
- ✅ Générer des arguments variés sur un sujet
- ✅ Tester des hypothèses sur des corrélations
- ✅ Créer des scénarios narratifs (worldbuilding)

### Ce que VoxPopulAI ne fait PAS

- ❌ Prédire des élections réelles
- ❌ Remplacer des sondages professionnels
- ❌ Fournir des données sociologiques validées
- ❌ Garantir la représentativité statistique

### Biais connus

- **Biais LLM** : Les modèles peuvent avoir des biais de training
- **Biais de génération** : Les personas reflètent les stéréotypes des données de training
- **Biais de question** : La formulation influence fortement les résultats

**Utiliser comme outil d'exploration, pas comme vérité absolue.**
