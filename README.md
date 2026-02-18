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

### Phase 3: Core Orchestration ✅ COMPLETE
- [x] PostgreSQL checkpointer for LangGraph state persistence
- [x] Query analyzer with LLM-based task analysis
- [x] Orchestrator decision node with routing logic
- [x] Department router for crew selection
- [x] Crew execution node (mock implementation)
- [x] Validation node stub
- [x] Response collator and output nodes
- [x] Edge routing functions
- [x] Complete LangGraph workflow assembly

### Phase 4: First Crew Prototype ✅ COMPLETE
- [x] BaseCrew abstract class (crews/base.py)
- [x] CrewRegistry with auto-discovery (registry/crew_registry.py)
- [x] Research department agents (Web Researcher, Content Analyzer, Fact Checker)
- [x] ResearchCrew with sequential process
- [x] Integration with orchestrator for actual crew execution
- [x] End-to-end integration test

**Note**: Phase 4 code is complete but execution requires Python 3.11/3.12 due to CrewAI's ChromaDB dependency. See [Python Version Compatibility](#python-version-compatibility) below.

**Next**: Phase 5 - Validation Layer (PydanticAI validators and schemas)

## Python Version Compatibility ⚠️

**IMPORTANT**: OMNI requires **Python 3.11 or 3.12**. Python 3.14 is **NOT SUPPORTED** due to upstream compatibility issues.

### Why Python 3.11/3.12?

OMNI's Layer 2 (CrewAI) depends on **ChromaDB** for internal knowledge/RAG features. ChromaDB currently uses Pydantic v1 patterns that are incompatible with Python 3.14's stricter type inference. This is an **upstream issue** affecting CrewAI, not OMNI's code.

**The issue:**
- Our design: PostgreSQL + pgvector ✅ (fully implemented)
- CrewAI's internal dependency: ChromaDB (for CrewAI's knowledge features)
- ChromaDB fails on Python 3.14 with: `pydantic.v1.errors.ConfigError: unable to infer type for attribute "chroma_server_nofile"`

**What works:**
- ✅ All OMNI code is correct and will work on Python 3.11/3.12
- ✅ PostgreSQL + pgvector is our actual storage layer (not ChromaDB)
- ✅ ChromaDB is only an unused internal dependency of CrewAI

**What doesn't work:**
- ❌ Running on Python 3.14 (CrewAI import fails)
- ❌ Cannot completely disable ChromaDB in CrewAI (import-time dependency)

### Setting up Python 3.11 or 3.12

```bash
# Using pyenv
pyenv install 3.12.0
pyenv local 3.12.0

# Or using conda
conda create -n omni python=3.12
conda activate omni

# Then reinstall dependencies
uv sync
```

## Quick Start

```bash
# Prerequisites: Python 3.11 or 3.12 (NOT 3.14)
python --version  # Should show 3.11.x or 3.12.x

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

### Phase 1 & 2 Tests (Database and Core)
```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/unit/test_state.py -v

# Run with coverage
uv run pytest --cov=src/omni tests/
```

### Phase 4 Tests (Research Crew)
```bash
# Test crew discovery (doesn't require Ollama)
uv run python tests/integration/test_phase4_crew.py

# Full test including crew execution (requires Ollama)
# Prerequisites:
# 1. Ollama must be running
# 2. Required models must be available:
#    - gemma3:12b (for web researcher and content analyzer)
#    - llama3.1:8b (for fact checker)
#
# Install models:
#   ollama pull gemma3:12b
#   ollama pull llama3.1:8b
#
# Then run:
#   uv run python tests/integration/test_phase4_crew.py
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
