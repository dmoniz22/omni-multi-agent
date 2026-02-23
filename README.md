# OMNI Multi-Agent Orchestration System

A production-ready, locally-deployed multi-agent orchestration system built on a three-layer architecture:

- **Layer 1 — LangGraph**: High-level workflow orchestrator (the "CEO") managing state, routing, branching, loops, retries, and human-in-the-loop
- **Layer 2 — CrewAI**: Department-level execution (the "Departments") with specialist agents collaborating on subtasks
- **Layer 3 — PydanticAI**: Validation and quality assurance (the "Legal/QA Team") ensuring type-safe data at every handoff

All LLM inference runs on **Ollama** locally.

## Implementation Status

### Phase 1-4: Foundation ✅ COMPLETE
- Project initialization with uv
- All dependencies installed (LangGraph, CrewAI, PydanticAI, FastAPI)
- Full directory structure created
- PostgreSQL with pgvector in Docker
- Core modules (constants, exceptions, config, state, models, logging)
- LangGraph workflow with checkpointer
- First Crew (Research department)

### Phase 5: Validation Layer ✅ COMPLETE
- PydanticAI validators and schemas
- InputValidator, OutputValidator, ResponseValidator
- ValidatorRegistry with auto-discovery

### Phase 6: Dynamic Routing ✅ COMPLETE
- Orchestrator uses real LLM (qwen3:14b)
- ContextManager for context window management

### Phase 7: Multi-Crew Expansion ✅ COMPLETE
- 6 crews: Research, GitHub, Social, Analysis, Writing, Coding
- Auto-discovery via CrewRegistry

### Phase 8: Skills/Tools System ✅ COMPLETE
- BaseSkill class with action definitions
- SkillRegistry for discovery and execution
- 5 skills: File, Calculator, Search, Browser, GitHub

### Phase 9: Memory System ✅ COMPLETE
- ShortTermMemory (LangGraph checkpoints)
- LongTermMemory (pgvector embeddings)
- ContextManager for context window

### Phase 10: API Layer ✅ COMPLETE
- FastAPI application with CORS
- Health endpoints (/health, /health/ready, /health/live)
- Task endpoints (create, get, delete)
- Session endpoints (create, get, delete)

### Phase 11-12: Deployment & Testing ✅ COMPLETE
- Dockerfile for OMNI app
- docker-compose.yml with PostgreSQL + App services
- Final integration tests

## Quick Start

### Prerequisites
- Python 3.12
- Docker & Docker Compose
- Ollama with qwen3:14b model

### Setup

```bash
# 1. Clone and navigate to project
cd omni

# 2. Start PostgreSQL
docker-compose up -d postgres

# 3. Run migrations
uv run alembic upgrade head

# 4. Start Ollama (separate terminal)
ollama serve
ollama pull qwen3:14b

# 5. Start the application
uv run python -m omni.main
```

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f app
```

The API will be available at `http://localhost:8000`

## Accessing the Application

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `http://localhost:8000/health` | Health check |
| `http://localhost:8000/docs` | Swagger API documentation |
| `http://localhost:8000/tasks` | Task management |
| `http://localhost:8000/sessions` | Session management |

### Swagger UI

Open `http://localhost:8000/docs` in your browser to explore and test the API interactively.

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
│   ├── crews/          # CrewAI departments (Research, GitHub, Social, Analysis, Writing, Coding)
│   ├── validators/     # PydanticAI validation
│   ├── skills/         # Tool ecosystem (File, Calculator, Search, Browser, GitHub)
│   ├── db/             # Database layer
│   ├── memory/         # Memory management
│   ├── api/            # FastAPI backend
│   └── main.py         # Entry point
├── config/             # YAML configuration files
├── docker/             # Docker configurations
├── tests/              # Test suite
└── migrations/         # Database migrations
```

## Configuration

Environment variables (see `.env.example`):
- `DATABASE_URL` - PostgreSQL connection string
- `OLLAMA_BASE_URL` - Ollama API endpoint (default: http://localhost:11434)

## License

MIT
