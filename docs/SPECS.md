# VoxPopulAI - Spécifications

> Simulateur de vote par population synthétique propulsé par LLM.

---

## Pourquoi VoxPopulAI

VoxPopulAI est un **laboratoire d'expérimentation sur les LLMs**. Il permet d'observer comment un même modèle de langage produit des réponses différentes lorsqu'on lui attribue des personas variés, et d'explorer les patterns, biais et limites de la génération conditionnée.

### Ce qu'on peut observer

| Phénomène | Ce que ça révèle |
| --------- | ---------------- |
| **Variation par contexte** | Comment un changement d'attributs (âge, profession, alignement D&D) modifie la réponse générée |
| **Cohérence des raisonnements** | Les arguments produits sont-ils véritablement liés au persona ou des clichés de l'entraînement ? |
| **Biais de génération** | Quels stéréotypes le modèle reproduit-il spontanément ? |
| **Limites de conditionnement** | Jusqu'où le "persona" influence-t-il réellement la sortie ? |
| **Worldbuilding créatif** | Peut-on générer des dynamiques narratives cohérentes (votes dans un univers fictif) ? |

### Ce que ça n'est PAS

- ❌ Un outil de sondage ou de prédiction électorale
- ❌ Une étude sociologique valide
- ❌ Une simulation fidèle de la réalité
- ❌ Une source de vérité sur les opinions réelles des populations

Les résultats sont des **artefacts de génération LLM** — utiles pour comprendre les modèles, inutiles pour comprendre la société.

---

## Scénarios illustrés

### Scénario 1 — "Référendum sur les smartphones à l'école"

**Objectif d'exploration** : Observer comment le LLM génère des positions différentes selon les attributs démographiques attribués, et identifier les patterns stéréotypés.

```
Question : "Faut-il interdire les smartphones dans les écoles ?"

→ Profil : grand_public_france
→ Nombre de personas : 500

Observation :
  Phase 1 — Génération : 500 personas avec attributs variés
  Phase 2 — Vote : chaque persona génère une réponse conditionnée
  
  Exemples de générations :
  
  Marie Dubois (45 ans, cadre, 2 enfants) :
    Position : OUI
    Raisonnement : "En tant que mère, je vois l'addiction aux écrans.
                    Mes enfants sont déjà trop connectés."
    → Note : Le modèle associe "parent + 45 ans" à l'inquiétude sur les écrans
  
  Lucas Martin (22 ans, étudiant) :
    Position : NON  
    Raisonnement : "C'est un outil pédagogique. Les interdire c'est
                    nier l'évolution technologique."
    → Note : Le modèle associe "étudiant + 22 ans" à la défense technophile
  
  Résultat agrégé :
    OUI : 67% (335 votes)
    NON : 23% (115 votes)
    ABSTENTION : 10% (50 votes)
  
  Patterns observés :
    - Parents d'enfants : +66% de votes OUI
    - 18-24 ans : majoritairement NON
    - CSP+ : corrélation OUI plus forte que chez ouvriers
    
  Ce que ça montre :
    Le modèle reproduit des stéréotypes sociétaux dans ses générations.
    Ces corrélations reflètent les patterns de l'entraînement, pas la réalité.
```

### Scénario 2 — "Développeurs et déploiement automatique"

**Objectif d'exploration** : Tester jusqu'où le conditionnement par "expérience" et "rôle" influence la réponse générée dans un domaine technique.

```
Question : "Êtes-vous favorable au déploiement automatique sans
            review humaine pour les hotfixes critiques ?"

→ Profil : developpeurs
→ Nombre : 100

Observation :
  
  Senior DevOps (12 ans exp) :
    Position : OUI (avec conditions)
    Raisonnement : "Si tests auto complets + rollback instantané,
                    c'est plus sûr qu'un humain pressé à 3h du mat."
    → Le modèle associe "DevOps + senior" à l'automatisation pragmatique
  
  Junior Frontend (2 ans exp) :
    Position : NON
    Raisonnement : "Trop risqué. J'ai déjà cassé la prod en pensant
                    que mon fix était simple. Review obligatoire."
    → Le modèle associe "junior + frontend" à la prudence et aux échecs passés
  
  Lead Architect (15 ans exp) :
    Position : ABSTENTION
    Raisonnement : "Dépend du contexte. Hotfix oui, feature non.
                    Trop nuancé pour une réponse binaire."
    → Le "lead" génère plus de nuance — est-ce un vrai raisonnement
      ou un stéréotype de "sagesse hiérarchique" ?

  Résultat agrégé :
    OUI : 35%
    NON : 45%
    ABSTENTION : 20%
  
  Patterns :
    - "Seniorité" inversement corrélée avec opposition
    - "DevOps" ≠ "Frontend" dans les positions générées
    
  Ce que ça montre :
    Le LLM reproduit des stéréotypes de l'industrie tech.
    La "position" est générée à partir du label de rôle, pas d'une expertise réelle.
```

### Scénario 3 — "Vote dans l'univers D&D"

**Objectif d'exploration** : Tester la cohérence narrative — peut-on générer un système politique fictif où les réponses respectent la logique interne de l'univers ?

```
Contexte : Faerûn, D&D 5e
Question : "Le conseil des guildes doit-il autoriser la magie 
            nécromancienne dans Waterdeep ?"

→ Profil : donjon_et_dragon
→ Nombre : 50

Observation :

VoxPopulAI génère 50 aventuriers avec alignements et classes :
- 5 paladins (Loyal Bon) → majoritairement CONTRE (cohérent avec alignement)
- 8 magiciens (dont 2 nécromanciens) → majoritairement POUR (cohérent)
- 3 clercs de Kelemvor → FERMEMENT CONTRE (cohérent avec déité)
- 6 roublards → majoritairement ABSTENTION ("pas leur problème")

Résultat :
  OUI : 30% (magiciens, certains warlocks)
  NON : 55% (paladins, clercs, rôdeurs)
  ABSTENTION : 15% (roublards, barbares)

Analyse :
  - Alignement détermine ~80% des votes
  - Classes liées à la magie arcane plus favorables
  - Le LLM respecte la cohérence de l'univers (pas de paladin pro-nécromancie)
  
Ce que ça montre :
  Le conditionnement par "alignement" et "classe" fonctionne bien
  pour la cohérence narrative. Le modèle applique correctement
  les règles implicites de l'univers D&D.
  
Usage : création de dynamiques politiques pour campagnes RPG.
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

### Ce que VoxPopulAI révèle

- ✅ Comment les LLMs conditionnent leurs réponses selon le contexte attribué
- ✅ Les stéréotypes et patterns que le modèle reproduit spontanément
- ✅ La cohérence (ou l'absence de cohérence) des raisonnements générés
- ✅ L'efficacité du "role prompting" pour guider les sorties
- ✅ La variabilité des réponses à question identique selon le persona

### Ce que VoxPopulAI ne fait PAS

- ❌ Prédire des comportements humains réels
- ❌ Fournir des données sociologiques validées
- ❌ Remplacer des études empiriques ou des sondages
- ❌ Simuler fidèlement la réalité démographique
- ❌ Garantir la représentativité statistique de quoi que ce soit

### Ce que les résultats représentent vraiment

Les votes générés sont des **artefacts du modèle de langage** utilisé. Ils reflètent :

- Les biais et patterns de l'entraînement du LLM
- Les stéréotypes présents dans les données de training
- La capacité du modèle à suivre des instructions de conditionnement
- Les corrélations statistiques apprises (pas nécessairement les corrélations réelles)

### Interprétation correcte

**Incorrect** : "Les parents français sont favorables à 67% à l'interdiction des smartphones"

**Correct** : "Le modèle qwen3:14b, lorsqu'on lui attribue le persona 'parent français', génère une réponse 'OUI' dans 67% des cas sur cette question"

### Biais et limitations connus

| Source | Impact |
|--------|--------|
| **Biais de training** | Le LLM reproduit les stéréotypes de ses données d'entraînement |
| **Biais de génération** | Les personas sont des constructions textuelles, pas des individus simulés |
| **Biais de question** | La formulation influence fortement les réponses générées |
| **Coût computationnel** | Échantillon limité par les ressources (temps, GPU) |
| **Déterminisme partiel** | Mêmes seeds ≠ mêmes résultats exacts (sampling aléatoire) |

**À utiliser comme outil d'expérimentation sur les LLMs, pas comme base pour des décisions réelles.**
