# OMNI Multi-Agent Orchestration System

A production-ready, locally-deployed multi-agent orchestration system built on a three-layer architecture:

- **Layer 1 — LangGraph**: High-level workflow orchestrator (the "CEO") managing state, routing, branching, loops, retries, and human-in-the-loop
- **Layer 2 — CrewAI**: Department-level execution (the "Departments") with specialist agents collaborating on subtasks
- **Layer 3 — PydanticAI**: Validation and quality assurance (the "Legal/QA Team") ensuring type-safe data at every handoff

## Architecture

```
User Input → LangGraph Orchestrator → CrewAI Department → PydanticAI Validation → Response
```

All LLM inference runs on **Ollama** locally.

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

## Project Structure

```
omni/
├── src/omni/           # Main application code
│   ├── core/           # Core infrastructure
│   ├── orchestrator/   # LangGraph workflow
│   ├── crews/          # CrewAI departments
│   ├── validators/     # PydanticAI validation
│   ├── skills/         # Tool ecosystem
│   ├── db/             # Database layer
│   ├── memory/         # Memory management
│   ├── api/            # FastAPI backend
│   └── dashboard/      # Gradio web UI
├── config/             # YAML configuration files
├── tests/              # Test suite
└── migrations/         # Database migrations
```

## Configuration

See `config/` directory for YAML configuration files:
- `settings.yaml` - Global system settings
- `models.yaml` - Model definitions and routing
- `departments.yaml` - Department/crew definitions
- `skills.yaml` - Skill registry configuration

## License

MIT
