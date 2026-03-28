# VoxPopulAI - Roadmap

> **Tout développement doit être rattaché à une issue GitHub.**

---

## MVP (Complete)

Fonctionnalités core extraites du projet ATEAM et stabilisées.

<details>
<summary>Terminé (core features)</summary>

### Voting System
- [x] Vote synchrone (POST /api/vote/) — extraction depuis ATEAM
- [x] Vote streaming SSE (POST /api/vote/stream)
- [x] Vote asynchrone (POST /api/vote/async)
- [x] Orchestration complète (personas → votes → analyse)
- [x] Modèles Pydantic (Vote, Tally, Analysis, Result)

### Persona System
- [x] Génération LLM avec attributs pondérés
- [x] Persistance SQLite (personas.db)
- [x] Génération de noms réalistes (INSEE)
- [x] Validation qualité par LLM juge
- [x] Store avec CRUD et échantillonnage

### Profiles
- [x] Registry avec auto-découverte JSON
- [x] Profil grand_public_france (INSEE)
- [x] Profil experts (multidisciplinaire)
- [x] Profil developpeurs (tech industry)
- [x] Profil donjon_et_dragon (D&D)

### Infrastructure
- [x] FastAPI backend avec routes
- [x] SPA vanilla JS (Vote, Personas, History, Settings)
- [x] File d'attente LLM priorisée
- [x] Extraction JSON des réponses
- [x] Event Log SQLite (audit trail)

### Documentation
- [x] README avec quick start
- [x] CLAUDE.md guide développement
- [x] ARCHITECTURE.md diagrammes ASCII
- [x] SPECS.md scénarios et API
- [x] BEST_PRACTICES.md standards
- [x] ROADMAP.md (ce fichier)

</details>

---

## Phase 1 — Tests & Qualité (En cours)

> Couverture 80%+, CI/CD, robustesse

### Testing
- [ ] Tests unitaires vote/orchestrator.py
- [ ] Tests unitaires personas/generator.py
- [ ] Tests unitaires personas/store.py
- [ ] Tests unitaires profiles/registry.py
- [ ] Tests unitaires llm/queue.py
- [ ] Tests unitaires llm/json_utils.py
- [ ] Tests API endpoints (FastAPI TestClient)
- [ ] CI/CD GitHub Actions (pytest, ruff, pre-commit)
- [ ] Coverage badge dans README

### Robustesse
- [ ] Circuit breaker pour Ollama API (retry + fallback)
- [ ] Timeouts configurables pour LLM calls
- [ ] Gestion gracieuse des erreurs Ollama (modèle manquant, GPU overload)
- [ ] Validation des settings au startup
- [ ] Health check endpoint (/health)

### Frontend
- [ ] Tests de bout en bout (Playwright ou Cypress)
- [ ] Gestion erreurs réseau (retry, feedback utilisateur)
- [ ] Loading states pour toutes les opérations async
- [ ] Toast notifications pour succès/erreurs
- [ ] Responsive design improvements

---

## Phase 2 — Features Vote (À planifier)

> Améliorations du système de vote

### Analyse
- [ ] Visualisations charts (Chart.js ou D3)
  - [ ] Répartition votes (pie/bar)
  - [ ] Cross-tabs par attribut (stacked bar)
  - [ ] Word cloud des raisonnements
- [ ] Export résultats (CSV, JSON, PDF)
- [ ] Comparaison sessions (diff entre 2 votes)

### Vote avancé
- [ ] Vote pondéré (poids démographiques)
- [ ] Multi-questions (sondage complet)
- [ ] Vote conditionnel (si X alors question Y)
- [ ] Historique temporel (évolution opinion)

---

## Phase 3 — Personas & Profiles (À planifier)

> Améliorations génération personas

### Personas
- [ ] Interface édition persona (UI)
- [ ] Duplication persona
- [ ] Tags/categories personas
- [ ] Recherche personas par attributs
- [ ] Clustering personas (similarité)

### Profiles
- [ ] UI création profil custom
- [ ] Import/export profils (JSON)
- [ ] Profils internationaux (US, UK, DE...)
- [ ] Profils historiques (France 1950, 1980...)

---

## Phase 4 — Scale & Production (À planifier)

> Prêt pour usage production

### Database
- [ ] Support PostgreSQL (optionnel)
- [ ] Migrations Alembic
- [ ] Connection pooling
- [ ] Backup automatique personas.db

### Performance
- [ ] Cache personas fréquemment utilisés
- [ ] Batch LLM calls quand possible
- [ ] Compression events.db (rotation)
- [ ] Monitoring temps de réponse

### Sécurité
- [ ] Rate limiting API
- [ ] API key authentication (optionnel)
- [ ] CORS strict en production
- [ ] Audit complet (qui a fait quoi)

---

## Phase 5 — Documentation & Community (À planifier)

> Ressources pour utilisateurs

### Documentation utilisateur
- [ ] Guide utilisateur complet
- [ ] Tutoriels vidéo (screencasts)
- [ ] FAQ
- [ ] Troubleshooting guide

### Profils communautaires
- [ ] Repository de profils publics
- [ ] Template profil standardisé
- [ ] Documentation création profils

### Intégrations
- [ ] API REST documentée (OpenAPI/Swagger UI amélioré)
- [ ] Webhooks (notification vote terminé)
- [ ] Export vers Google Sheets/Excel

---

## Idées à explorer

### Non priorisé — à évaluer

- **Multi-modèles** : Vote avec ensemble de modèles (consensus LLM)
- **Personas vocaux** : Génération audio des opinions (TTS)
- **Debate mode** : Personas qui débattent entre eux avant de voter
- **Évolution** : Personas dont l'opinion évolue avec le temps
- **Analyse sémantique** : Clustering automatique des arguments
- **Prédiction** : Scoring de confiance sur la prédiction

---

## Notes

### Versionnement

Suivre [Semantic Versioning](https://semver.org/) :
- `0.1.0` — MVP (actuel)
- `0.2.0` — Tests & CI/CD
- `0.3.0` — Features vote avancées
- `0.4.0` — Personas & profiles améliorés
- `1.0.0` — Production ready

### Branches

- `main` — Stable, releases
- `dev` — Intégration features
- `issue-XXX-description` — Feature branches

### Process

1. Créer/prendre une issue
2. Brancher depuis `dev` : `git checkout -b issue-XXX-desc`
3. Développer avec tests
4. PR vers `dev` avec `closes #XXX`
5. Review + merge
6. Mise à jour ROADMAP.md
7. Release tag quand prêt

---

## Métriques cibles

| Métrique | Cible v1.0 | Actuel |
|----------|-----------|--------|
| Couverture tests | 80% | ~0% |
| Issues ouvertes | < 10 | - |
| Temps vote 100 personas | < 2 min | ~3 min |
| Uptime (si déployé) | 99.9% | N/A |

---

**Last Updated** : March 2024
