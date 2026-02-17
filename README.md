# OMNI Multi-Agent Orchestration System

A production-ready, locally-deployed multi-agent orchestration system built on a three-layer architecture:

- **Layer 1 — LangGraph**: High-level workflow orchestrator (the "CEO") managing state, routing, branching, loops, retries, and human-in-the-loop
- **Layer 2 — CrewAI**: Department-level execution (the "Departments") with specialist agents collaborating on subtasks
- **Layer 3 — PydanticAI**: Validation and quality assurance (the "Legal/QA Team") ensuring type-safe data at every handoff

All LLM inference runs on **Ollama** locally.

## Implementation Status

### Phase 1: Foundation ✅ COMPLETE
- [x] Project initialization with uv
- [x] All dependencies installed (LangGraph, CrewAI, PydanticAI, FastAPI, Gradio)
- [x] Full directory structure created
- [x] Configuration files (YAML configs, .env.example)
- [x] Core modules implemented (constants, exceptions, config, state, models, logging)
- [x] Unit tests (50 tests, all passing)

### Phase 2: Database Setup ✅ COMPLETE
- [x] PostgreSQL with pgvector in Docker
- [x] Alembic migrations configured with async SQLAlchemy
- [x] Database engine with connection pooling
- [x] SQLAlchemy ORM models (Session, Task, TaskStep, MemoryVector, AuditLog, Checkpoint)
- [x] Initial migration created and applied
- [x] Repository layer (Session, Task, TaskStep, Memory CRUD operations)
- [x] Integration tests for database operations
- [x] All tests passing

**Next**: Phase 3 - Core Orchestration (LangGraph workflow)

## Quick Start

```bash
# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start PostgreSQL (Docker)
docker-compose up -d postgres

# Run migrations
uv run alembic upgrade head

# Start the application
uv run python -m omni.main
```

## Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/unit/test_state.py -v

# Run with coverage
uv run pytest --cov=src/omni tests/
```

## Project Structure

```
omni/
├── src/omni/           # Main application code
│   ├── core/           # Core infrastructure (constants, config, state, models, logging)
│   ├── orchestrator/   # LangGraph workflow
│   ├── crews/          # CrewAI departments
│   ├── validators/     # PydanticAI validation
│   ├── skills/         # Tool ecosystem
│   ├── db/             # Database layer
│   ├── memory/         # Memory management
│   ├── api/            # FastAPI backend
│   └── dashboard/      # Gradio web UI
├── config/             # YAML configuration files
│   ├── settings.yaml   # System settings
│   ├── models.yaml     # Model assignments (runtime editable)
│   ├── departments.yaml # Department metadata
│   └── skills.yaml     # Skill registry
├── tests/              # Test suite
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── e2e/            # End-to-end tests
└── migrations/         # Database migrations
```

## Configuration

See `config/` directory for YAML configuration files:
- `settings.yaml` - Global system settings
- `models.yaml` - Model definitions and routing (editable at runtime via dashboard)
- `departments.yaml` - Department/crew definitions
- `skills.yaml` - Skill registry configuration

## License

MIT
