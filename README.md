# OMNI Multi-Agent Orchestration System

A production-ready, locally-deployed multi-agent orchestration system with OpenClaw-style computer automation capabilities.

## Architecture

- **Layer 1 — LangGraph**: High-level workflow orchestrator (the "CEO") managing state, routing, branching, loops, retries, and human-in-the-loop
- **Layer 2 — CrewAI**: Department-level execution (the "Departments") with specialist agents collaborating on subtasks
- **Layer 3 — PydanticAI**: Validation and quality assurance (the "Legal/QA Team") ensuring type-safe data at every handoff

All LLM inference runs on **Ollama** locally.

## OpenClaw-Style Capabilities

OMNI now supports **local computer automation** similar to OpenClaw:

### Skills (Tools)

| Skill | Description | Actions |
|-------|-------------|---------|
| **computer** | Mouse/keyboard control | move_mouse, click_mouse, type_text, press_key, hotkey, scroll_mouse, get_screen_size, get_mouse_position |
| **screenshot** | Screen capture | capture_screen, capture_window, analyze_screen, get_windows |
| **shell** | Command execution | run_command, run_script, get_processes, kill_process |
| **browser** | Playwright automation | navigate, click, type, press, screenshot, scrape, evaluate, get_html |
| **file** | File operations | read, write, list_dir |
| **calculator** | Math operations | calculate, convert |
| **search** | Web search | web_search, news_search |
| **github** | GitHub API | search_repos, get_repo, get_file, create_gist, list_issues |

### Crews (Departments)

| Crew | Purpose | Agents |
|------|---------|--------|
| **Research** | Web research, fact-checking | Web Researcher, Content Analyzer, Fact Checker |
| **GitHub** | Repository analysis, code review | GitHub Researcher, Code Analyst, Gist Creator |
| **Social** | Content creation | Content Creator, Engagement Optimizer, Analytics Monitor |
| **Analysis** | Data analysis | Data Analyst, Insight Generator, Report Creator |
| **Writing** | Articles, documentation | Editorial Agent, Long-form Writer, Social Writer |
| **Coding** | Code generation | Code Generator, Refactoring Agent, Architecture Agent |
| **Do** | Computer automation (OpenClaw mode) | Planner, Executor, Verifier |

## Quick Start

### Prerequisites

- Python 3.12
- Docker & Docker Compose
- Ollama with models (qwen3:14b, gemma3:12b, llama3.1:8b)

### Running with Docker

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f app
```

### Running Locally

```bash
# 1. Install dependencies
pip install -e .

# 2. Install additional automation dependencies
pip install pyautogui mss pygetwindow playwright
playwright install chromium

# 3. Start Ollama
ollama serve
ollama pull qwen3:14b gemma3:12b

# 4. Start the application
python -m omni.main
```

## Accessing the Application

| Service | URL |
|---------|-----|
| **Dashboard** | http://localhost:7860 |
| **API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |

## Model Configuration

Configure which Ollama models to use for different components:

- **Orchestrator Model**: The "brain" that decides which crew to use (qwen3:14b recommended)
- **Crew Models**: Individual models for each department's agents

The dashboard provides an easy interface to configure these settings.

## Project Structure

```
omni/
├── src/omni/
│   ├── core/           # Infrastructure (constants, config, state, models, logging)
│   ├── orchestrator/   # LangGraph workflow
│   ├── crews/         # CrewAI departments (7 crews including Do)
│   ├── validators/     # PydanticAI validation
│   ├── skills/        # Skills (9 skills including computer, screenshot, shell, browser)
│   ├── db/            # Database layer
│   ├── memory/        # Memory management
│   ├── api/           # FastAPI backend
│   └── dashboard/     # Gradio dashboard
├── config/            # YAML configuration files
├── tests/             # Test suite
└── migrations/        # Database migrations
```

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `OLLAMA_BASE_URL` - Ollama API endpoint (default: http://localhost:11434)

## Dependencies

### Core
- langgraph
- crewai
- pydantic-ai
- fastapi
- ollama

### Automation (OpenClaw Features)
- pyautogui - Mouse/keyboard control
- mss - Screen capture
- pygetwindow - Window management
- playwright - Browser automation

## License

MIT
