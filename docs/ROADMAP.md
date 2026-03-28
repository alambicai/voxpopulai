# Roadmap

## Current Status

**Version**: 0.1.0  
**Phase**: MVP Complete - Core functionality operational

## Completed Features

### Core Voting System
- [x] Synchronous voting endpoint
- [x] Streaming voting with SSE progress
- [x] Asynchronous voting with status polling
- [x] Vote tally computation
- [x] LLM-based qualitative analysis
- [x] Session audit trail (events.db)

### Persona Management
- [x] Persona generation from demographic profiles
- [x] SQLite persistence (personas.db)
- [x] Name generation with French demographic data
- [x] Quality validation with judge model
- [x] Persona statistics and distribution queries

### Population Profiles
- [x] Profile registry system
- [x] grand_public_france profile (INSEE data)
- [x] experts profile (multidisciplinary panel)
- [x] developpeurs profile (software developers)
- [x] donjon_et_dragon profile (D&D adventurers)

### LLM Integration
- [x] Ollama API client
- [x] Priority queue for GPU management
- [x] JSON extraction from LLM responses
- [x] Retry logic with exponential backoff

### Frontend
- [x] Vanilla JavaScript SPA
- [x] Hash-based routing
- [x] Vote creation and viewing
- [x] Persona management interface
- [x] Session history browser
- [x] Settings configuration
- [x] Real-time progress via SSE

### Infrastructure
- [x] FastAPI application structure
- [x] Pydantic data models
- [x] Settings persistence (JSON)
- [x] Pre-commit hooks
- [x] Ruff linting configuration
- [x] Pytest configuration

### Documentation
- [x] ARCHITECTURE.md
- [x] SPECS.md
- [x] BEST_PRACTICES.md
- [x] ROADMAP.md (this file)

---

## In Progress

None currently.

---

## Upcoming Features

### Phase 1: Stability & Polish (Next 2-4 weeks)

#### Testing & Quality
- [ ] Unit tests for core modules (vote, personas, profiles)
- [ ] Integration tests for API endpoints
- [ ] Test coverage reporting (target: 80%)
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Load testing for concurrent voting sessions

#### Error Handling & Reliability
- [ ] Better error messages for LLM failures
- [ ] Circuit breaker pattern for Ollama API
- [ ] Database connection pooling
- [ ] Graceful shutdown handling
- [ ] Request timeout management

#### Frontend Improvements
- [ ] Loading states for all async operations
- [ ] Error toast notifications
- [ ] Mobile responsiveness improvements
- [ ] Dark/light theme toggle
- [ ] Keyboard shortcuts

### Phase 2: Enhanced Features (1-2 months)

#### Advanced Voting
- [ ] Weighted voting (demographic weighting)
- [ ] Multi-question surveys
- [ ] Conditional logic (branching questions)
- [ ] Time-based voting (simulate opinion evolution)
- [ ] Export results (CSV, JSON, PDF)

#### Persona Enhancements
- [ ] Persona editing interface
- [ ] Custom profile creation UI
- [ ] Import/export profiles (JSON)
- [ ] Persona preview before voting
- [ ] Persona clustering (find similar personas)

#### Analysis & Visualization
- [ ] Interactive charts (Chart.js or D3)
- [ ] Demographic breakdown visualizations
- [ ] Word cloud from vote reasoning
- [ ] Sentiment analysis of opinions
- [ ] Compare multiple sessions side-by-side

### Phase 3: Scale & Integration (2-3 months)

#### Database Migration
- [ ] PostgreSQL support
- [ ] Database migration system (Alembic)
- [ ] Read replicas for queries
- [ ] Backup and restore utilities

#### API & Integration
- [ ] Webhook support for vote completion
- [ ] API rate limiting
- [ ] API key authentication
- [ ] OpenAPI documentation improvements
- [ ] GraphQL endpoint (optional)

#### LLM Enhancements
- [ ] Multi-model ensemble voting
- [ ] Support for commercial APIs (OpenAI, Anthropic)
- [ ] Local model caching
- [ ] Prompt versioning and A/B testing
- [ ] Fine-tuning support for custom personas

### Phase 4: Enterprise Features (3-6 months)

#### Multi-tenancy
- [ ] Organization/workspaces
- [ ] User authentication (OAuth, SSO)
- [ ] Role-based access control
- [ ] Resource quotas per organization

#### Collaboration
- [ ] Share sessions via public links
- [ ] Comments on voting sessions
- [ ] Collaborative profile editing
- [ ] Team voting (aggregate team opinions)

#### Advanced Analytics
- [ ] Trend analysis across sessions
- [ ] Statistical significance testing
- [ ] Predictive modeling
- [ ] Custom report builder

### Phase 5: Platform Extensions (6+ months)

#### Deployment Options
- [ ] Docker Compose production setup
- [ ] Kubernetes manifests
- [ ] Cloud deployment guides (AWS, GCP, Azure)
- [ ] Managed hosting option

#### Plugin System
- [ ] Custom persona generators
- [ ] Custom analysis modules
- [ ] Integration plugins (Slack, Discord, etc.)
- [ ] Webhook plugins

#### Mobile
- [ ] React Native or Flutter app
- [ ] Push notifications for async votes
- [ ] Offline mode with sync

---

## Technical Debt

### Current Items

- [ ] `tests/` directory is empty - need comprehensive test suite
- [ ] No database migrations - manual schema updates
- [ ] Hardcoded French names only - need internationalization
- [ ] SQLite file locking issues with concurrent writes
- [ ] Frontend uses vanilla JS - consider framework (React/Vue)
- [ ] No caching layer for expensive operations
- [ ] Limited observability (no metrics, basic logging)

### Refactoring Opportunities

- [ ] Extract common API patterns into base classes
- [ ] Create abstract LLM provider interface
- [ ] Implement proper dependency injection container
- [ ] Add database abstraction layer (SQLAlchemy?)
- [ ] Refactor frontend into component-based structure

---

## Research & Exploration

### Potential Directions

- **Reinforcement Learning**: Train models to better simulate specific demographics
- **Agent-based Simulation**: Multi-round interactions between personas
- **Real-time Collaboration**: WebSocket-based live voting sessions
- **Blockchain Integration**: Immutable vote records (probably overkill)
- **Voice/Video Personas**: Generate audio/video responses

### LLM Research

- [ ] Evaluate newer models (Llama 3.1, Qwen 2.5, etc.)
- [ ] Test smaller models for cost/performance balance
- [ ] Prompt optimization experiments
- [ ] Bias detection and mitigation
- [ ] Hallucination reduction techniques

---

## Bug Tracking

### Known Issues

- [ ] #1 - SSE connection drops on long-running votes (>5 min)
- [ ] #2 - Memory leak in persona generation with large counts
- [ ] #3 - Judge model occasionally rejects valid personas
- [ ] #4 - Cross-tab audit slow with 1000+ personas
- [ ] #5 - Frontend doesn't handle 503 errors gracefully

---

## Release Planning

### v0.2.0 - Testing & Stability
**Target**: 1 month  
**Focus**: Test coverage, error handling, reliability

### v0.3.0 - Enhanced Voting
**Target**: 2 months  
**Focus**: Weighted voting, surveys, exports

### v0.4.0 - Analysis & Visualization
**Target**: 3 months  
**Focus**: Charts, reports, comparisons

### v1.0.0 - Production Ready
**Target**: 6 months  
**Focus**: PostgreSQL, auth, enterprise features

---

## Contribution Guidelines

Want to help? Priority areas:

1. **Testing**: Write unit tests for existing code
2. **Documentation**: Improve inline docs and examples
3. **Profiles**: Create new population profiles
4. **Frontend**: UI/UX improvements
5. **Performance**: Profiling and optimization

See `BEST_PRACTICES.md` for development workflow.

---

## Notes

- This roadmap is aspirational and subject to change based on user feedback
- Items marked with 🎯 are high priority
- Security features prioritized before v1.0
- Mobile app considered for post-v1.0

**Last Updated**: March 27, 2024
