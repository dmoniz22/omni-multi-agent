"""Gradio dashboard for OMNI."""

import gradio as gr
import json
import os
import yaml
from pathlib import Path

from omni.core.logging import get_logger

logger = get_logger(__name__)

# Initialize database on module load
try:
    from omni.db.engine import init_db
    import asyncio

    asyncio.run(init_db())
    logger.info("Database initialized for dashboard")
except Exception as e:
    logger.warning(f"Could not initialize database: {e}")

MODELS_CONFIG_PATH = (
    Path(__file__).parent.parent.parent.parent / "config" / "models.yaml"
)

OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


def get_available_models():
    """Get available Ollama models."""
    try:
        import httpx

        response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        pass
    return ["qwen3:14b", "llama3.1:8b", "gemma3:12b"]


def get_all_available_models():
    """Get all available models including cloud providers."""
    models = []

    # Get Ollama models
    ollama_models = get_available_models()
    for m in ollama_models:
        models.append(f"ollama:{m}")

    # Get cloud models from config
    config = load_model_config()
    providers = config.get("providers", {})

    if providers.get("openai"):
        models.extend(["openai:gpt-4o", "openai:gpt-4o-mini", "openai:o1"])

    if providers.get("anthropic"):
        models.extend(["anthropic:claude-3-5-sonnet", "anthropic:claude-3-haiku"])

    return models


CLOUD_MODELS = {
    "openai": ["gpt-4o", "gpt-4o-mini", "o1", "o1-mini"],
    "anthropic": ["claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku"],
}


def load_model_config():
    """Load model configuration from YAML file."""
    try:
        if MODELS_CONFIG_PATH.exists():
            with open(MODELS_CONFIG_PATH, "r") as f:
                return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Failed to load model config: {e}")
    return {}


def save_model_config(config):
    """Save model configuration to YAML file."""
    try:
        with open(MODELS_CONFIG_PATH, "w") as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        logger.warning(f"Failed to save model config: {e}")
        return False


def get_crew_agents(crew_name):
    """Get agents for a specific crew."""
    agents_map = {
        "Research": ["web_researcher", "content_analyzer", "fact_checker"],
        "GitHub": ["researcher", "code_analyst", "gist_creator"],
        "Social": ["content_creator", "engagement_optimizer", "analytics_monitor"],
        "Analysis": ["data_analyst", "insight_generator", "report_creator"],
        "Writing": ["editorial", "longform", "social_media"],
        "Coding": ["generator", "refactorer", "architect"],
    }
    return agents_map.get(crew_name, [])


def create_dashboard() -> gr.Blocks:
    """Create the OMNI Gradio dashboard."""

    with gr.Blocks(title="OMNI Dashboard") as dashboard:
        gr.Markdown("# OMNI Multi-Agent Orchestration System")
        gr.Markdown(
            "Manage tasks, configure models, and interact with the orchestration system."
        )

        with gr.Tab("Tasks"):
            gr.Markdown("## Submit a Task")
            with gr.Row():
                task_input = gr.Textbox(
                    label="Task Description",
                    placeholder="Enter your task (e.g., 'Research the latest AI news and create a summary')",
                    lines=3,
                )
            with gr.Row():
                submit_btn = gr.Button("Submit Task", variant="primary")
                clear_btn = gr.Button("Clear")
            task_output = gr.Textbox(label="Result", lines=10)

            with gr.Accordion("📚 Past Tasks", open=False):
                gr.Markdown("View and resume previous tasks from the database.")

                with gr.Row():
                    view_tasks_btn = gr.Button("Load Past Tasks", variant="secondary")

                past_tasks_output = gr.JSON(label="Your Task History")

                def load_past_tasks():
                    """Load past tasks from database."""
                    try:
                        import asyncio
                        from omni.memory import get_long_term_memory

                        async def get_tasks():
                            memory = get_long_term_memory()
                            # Get a default session or recent tasks
                            tasks = await memory.get_session_tasks(
                                session_id="default",
                                limit=20,
                            )
                            return [t.model_dump() for t in tasks]

                        tasks = asyncio.run(get_tasks())
                        if not tasks:
                            return {
                                "message": "No past tasks found. Tasks will be saved after execution."
                            }
                        return {"tasks": tasks}
                    except Exception as e:
                        return {
                            "error": str(e),
                            "message": "Database may not be available. Make sure PostgreSQL is running.",
                        }

                view_tasks_btn.click(
                    fn=load_past_tasks,
                    outputs=past_tasks_output,
                )

            def submit_task(task: str):
                """Execute task through the orchestrator."""
                if not task.strip():
                    return "Please enter a task."

                import httpx

                try:
                    response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5)
                    if response.status_code != 200:
                        return f"Error: Cannot connect to Ollama at {OLLAMA_URL}"
                except Exception as e:
                    return f"Error: Cannot connect to Ollama at {OLLAMA_URL}\n\nDetails: {str(e)}\n\nMake sure Ollama is running on your host machine."

                try:
                    import asyncio
                    from omni.orchestrator.graph import get_workflow
                    from omni.core.state import create_initial_state
                    from omni.memory import get_long_term_memory
                    import uuid

                    task_id = str(uuid.uuid4())
                    session_id = str(uuid.uuid4())

                    # Save task to database
                    async def save_task_to_db():
                        memory = get_long_term_memory()
                        await memory.save_task(
                            session_id=session_id,
                            task_id=task_id,
                            original_task=task,
                            status="running",
                        )

                    # Try to save task (may fail if DB not available)
                    try:
                        asyncio.run(save_task_to_db())
                    except Exception as db_err:
                        print(f"Warning: Could not save task to database: {db_err}")

                    initial_state = create_initial_state(
                        task_id=task_id,
                        session_id=session_id,
                        original_task=task,
                    )

                    async def run_workflow():
                        workflow = get_workflow()
                        return await workflow.ainvoke(initial_state)

                    result = asyncio.run(run_workflow())

                    final_output = result.get(
                        "final_response", result.get("final_output", {})
                    )

                    # Update task in database
                    async def update_task_in_db():
                        memory = get_long_term_memory()
                        await memory.update_task(
                            task_id=task_id,
                            status="completed",
                            final_response=final_output,
                            execution_summary=result.get("execution_summary", {}),
                        )

                    try:
                        asyncio.run(update_task_in_db())
                    except Exception as db_err:
                        print(f"Warning: Could not update task in database: {db_err}")

                    return (
                        f"Task: {task}\n\nResult:\n{json.dumps(final_output, indent=2)}"
                    )
                except Exception as e:
                    return f"Error executing task: {str(e)}"

            submit_btn.click(
                fn=submit_task,
                inputs=task_input,
                outputs=task_output,
            )
            clear_btn.click(
                fn=lambda: ("", ""),
                outputs=[task_input, task_output],
            )

        with gr.Tab("Model Configuration"):
            gr.Markdown("## LLM Model Configuration")
            gr.Markdown(
                "Configure which Ollama models to use. "
                "The Orchestrator decides HOW to complete tasks. "
                "Crew agents actually DO the work."
            )

            model_config = load_model_config()
            assignments = model_config.get("assignments", {})
            departments = assignments.get("departments", {})

            available_models = get_available_models()

            with gr.Row():
                ollama_url_input = gr.Textbox(
                    label="Ollama URL",
                    value=OLLAMA_URL,
                    placeholder="http://localhost:11434",
                )
                ollama_status = gr.Textbox(
                    label="Connection Status",
                    interactive=False,
                    value="Click Test to check",
                )

            def check_ollama_connection(url):
                try:
                    import httpx

                    response = httpx.get(f"{url}/api/tags", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        models = [m["name"] for m in data.get("models", [])]
                        return f"✅ {len(models)} models: {', '.join(models[:4])}{'...' if len(models) > 4 else ''}"
                    return f"⚠️ HTTP {response.status_code}"
                except Exception as e:
                    return f"❌ {str(e)}"

            gr.Button("Test Connection").click(
                fn=check_ollama_connection,
                inputs=ollama_url_input,
                outputs=ollama_status,
            )

            gr.Markdown("### 🤖 Orchestrator Model")
            gr.Markdown(
                "The 'brain' that decides which crew to use and how to complete tasks."
            )
            with gr.Row():
                orchestrator_dropdown = gr.Dropdown(
                    label="Orchestrator (Planning & Decisions)",
                    choices=available_models,
                    value=assignments.get("orchestrator", {}).get(
                        "decision", "qwen3:14b"
                    ),
                )

            gr.Markdown("### 👥 Crew Models")
            gr.Markdown("The models used by each crew's agents to do the actual work.")

            crew_model_configs = {}
            for crew_name in [
                "Research",
                "GitHub",
                "Social",
                "Analysis",
                "Writing",
                "Coding",
            ]:
                crew_key = crew_name.lower()
                crew_agents = departments.get(crew_key, {}).get("agents", {})
                default_model = (
                    crew_agents.get("researcher")
                    or crew_agents.get("web_researcher")
                    or crew_agents.get("content_creator")
                    or "qwen3:14b"
                )
                crew_model_configs[crew_name] = default_model

            with gr.Row():
                research_model = gr.Dropdown(
                    label="Research Crew (Web search, fact-checking)",
                    choices=available_models,
                    value=crew_model_configs.get("Research", "qwen3:14b"),
                )
                github_model = gr.Dropdown(
                    label="GitHub Crew (Repo analysis, code review)",
                    choices=available_models,
                    value=crew_model_configs.get("GitHub", "qwen3:14b"),
                )

            with gr.Row():
                social_model = gr.Dropdown(
                    label="Social Crew (Content creation)",
                    choices=available_models,
                    value=crew_model_configs.get("Social", "llama3.1:8b"),
                )
                analysis_model = gr.Dropdown(
                    label="Analysis Crew (Data analysis)",
                    choices=available_models,
                    value=crew_model_configs.get("Analysis", "gemma3:12b"),
                )

            with gr.Row():
                writing_model = gr.Dropdown(
                    label="Writing Crew (Articles, docs)",
                    choices=available_models,
                    value=crew_model_configs.get("Writing", "gemma3:12b"),
                )
                coding_model = gr.Dropdown(
                    label="Coding Crew (Code generation)",
                    choices=available_models,
                    value=crew_model_configs.get("Coding", "qwen2.5-coder:14b"),
                )

            gr.Markdown("### Current Settings")
            config_output = gr.JSON(
                value={
                    "ollama_url": OLLAMA_URL,
                    "orchestrator": assignments.get("orchestrator", {}).get(
                        "decision", "qwen3:14b"
                    ),
                    "crews": {
                        "research": crew_model_configs.get("Research"),
                        "github": crew_model_configs.get("GitHub"),
                        "social": crew_model_configs.get("Social"),
                        "analysis": crew_model_configs.get("Analysis"),
                        "writing": crew_model_configs.get("Writing"),
                        "coding": crew_model_configs.get("Coding"),
                    },
                }
            )

            def update_config(
                orch, research, github, social, analysis, writing, coding
            ):
                config = load_model_config()

                if "assignments" not in config:
                    config["assignments"] = {}

                config["assignments"]["orchestrator"] = {
                    "decision": orch,
                    "query_analyzer": orch,
                }

                if "departments" not in config["assignments"]:
                    config["assignments"]["departments"] = {}

                crew_configs = {
                    "research": {
                        "manager": research,
                        "agents": {
                            "web_researcher": research,
                            "content_analyzer": research,
                            "fact_checker": "llama3.1:8b",
                        },
                    },
                    "github": {
                        "manager": github,
                        "agents": {
                            "researcher": github,
                            "code_analyst": github,
                            "gist_creator": "qwen2.5-coder:14b",
                        },
                    },
                    "social": {
                        "manager": social,
                        "agents": {
                            "content_creator": social,
                            "engagement_optimizer": social,
                            "analytics_monitor": "gemma3:12b",
                        },
                    },
                    "analysis": {
                        "manager": analysis,
                        "agents": {
                            "data_analyst": analysis,
                            "insight_generator": analysis,
                            "report_creator": "llama3.1:8b",
                        },
                    },
                    "writing": {
                        "manager": writing,
                        "agents": {
                            "editorial": writing,
                            "longform": writing,
                            "social_media": "llama3.1:8b",
                        },
                    },
                    "coding": {
                        "manager": coding,
                        "agents": {
                            "generator": coding,
                            "refactorer": coding,
                            "architect": coding,
                        },
                    },
                }

                config["assignments"]["departments"] = crew_configs

                success = save_model_config(config)

                return {
                    "saved": success,
                    "orchestrator": orch,
                    "crews": {
                        "research": research,
                        "github": github,
                        "social": social,
                        "analysis": analysis,
                        "writing": writing,
                        "coding": coding,
                    },
                }

            save_btn = gr.Button("💾 Save Configuration", variant="primary")
            save_btn.click(
                fn=update_config,
                inputs=[
                    orchestrator_dropdown,
                    research_model,
                    github_model,
                    social_model,
                    analysis_model,
                    writing_model,
                    coding_model,
                ],
                outputs=config_output,
            )

            model_config = load_model_config()
            assignments = model_config.get("assignments", {})
            departments = assignments.get("departments", {})
            providers = model_config.get("providers", {})

            with gr.Row():
                gr.Markdown("### Connection Settings")

        with gr.Tab("Skills"):
            gr.Markdown("## Available Skills")
            gr.Markdown(
                "Test individual skills directly without going through the full orchestration."
            )

            with gr.Row():
                skill_choice = gr.Dropdown(
                    label="Select Skill",
                    choices=[
                        "calculator",
                        "file",
                        "search",
                        "browser",
                        "github",
                        "computer",
                        "screenshot",
                        "shell",  # New OpenClaw skills
                    ],
                    value="calculator",
                )

            with gr.Row():
                action_choice = gr.Dropdown(
                    label="Select Action",
                    choices=["calculate", "convert"],
                    value="calculate",
                )

            gr.Markdown("### Action Parameters")
            with gr.Row():
                params_input = gr.Textbox(
                    label="Parameters (JSON format)",
                    value='{"expression": "2 + 2"}',
                    lines=2,
                )

            with gr.Row():
                execute_btn = gr.Button("Execute Skill", variant="primary")

            result_output = gr.Textbox(label="Result", lines=5)

            # Map skills to their actions
            skill_actions = {
                "calculator": ["calculate", "convert"],
                "file": ["read", "write", "list_dir"],
                "search": ["web_search", "news_search"],
                "browser": [  # Playwright - full browser automation
                    "navigate",
                    "click",
                    "type",
                    "press",
                    "screenshot",
                    "scrape",
                    "evaluate",
                    "get_html",
                ],
                "github": [
                    "search_repos",
                    "get_repo",
                    "get_file",
                    "create_gist",
                    "list_issues",
                ],
                "computer": [  # OpenClaw - mouse/keyboard control
                    "move_mouse",
                    "click_mouse",
                    "type_text",
                    "press_key",
                    "hotkey",
                    "scroll_mouse",
                    "get_screen_size",
                    "get_mouse_position",
                ],
                "screenshot": [  # OpenClaw - screen capture
                    "capture_screen",
                    "capture_window",
                    "analyze_screen",
                    "get_windows",
                ],
                "shell": [  # OpenClaw - command execution
                    "run_command",
                    "run_script",
                    "get_processes",
                    "kill_process",
                ],
            }

            # Default params for each action
            default_params = {
                "calculator": {
                    "calculate": '{"expression": "2 + 2"}',
                    "convert": '{"value": 100, "from_unit": "c", "to_unit": "f"}',
                },
                "file": {
                    "read": '{"path": "test.txt"}',
                    "write": '{"path": "test.txt", "content": "Hello World"}',
                    "list_dir": '{"path": "."}',
                },
                "search": {
                    "web_search": '{"query": "AI news", "num_results": 5}',
                    "news_search": '{"query": "technology"}',
                },
                "browser": {  # Playwright defaults
                    "navigate": '{"url": "https://example.com", "wait_for": null}',
                    "click": '{"selector": "#submit"}',
                    "type": '{"selector": "#input", "text": "Hello", "clear_first": true}',
                    "press": '{"key": "Enter", "selector": null}',
                    "screenshot": '{"path": null, "full_page": false}',
                    "scrape": '{"url": "https://example.com", "selectors": null}',
                    "evaluate": '{"script": "return document.title"}',
                    "get_html": '{"selector": null}',
                },
                "github": {
                    "search_repos": '{"query": "python ai"}',
                    "get_repo": '{"owner": "microsoft", "repo": "TypeScript"}',
                },
                "computer": {  # OpenClaw defaults
                    "move_mouse": '{"x": 100, "y": 200, "duration": 0.5}',
                    "click_mouse": '{"x": 100, "y": 200, "button": "left"}',
                    "type_text": '{"text": "Hello World"}',
                    "press_key": '{"key": "enter", "presses": 1}',
                    "hotkey": '{"keys": ["ctrl", "c"]}',
                    "scroll_mouse": '{"clicks": 3}',
                    "get_screen_size": "{}",
                    "get_mouse_position": "{}",
                },
                "screenshot": {  # OpenClaw defaults
                    "capture_screen": '{"region": null}',
                    "capture_window": '{"title": ""}',
                    "analyze_screen": '{"prompt": "What do you see on screen?"}',
                    "get_windows": "{}",
                },
                "shell": {  # OpenClaw defaults
                    "run_command": '{"command": "ls -la", "timeout": 30}',
                    "run_script": '{"script": "echo Hello", "language": "bash"}',
                    "get_processes": '{"filter": null}',
                    "kill_process": '{"pid": 1234, "force": false}',
                },
            }

            # Default params for each action
            default_params = {
                "calculator": {
                    "calculate": '{"expression": "2 + 2"}',
                    "convert": '{"value": 100, "from_unit": "c", "to_unit": "f"}',
                },
                "file": {
                    "read": '{"path": "test.txt"}',
                    "write": '{"path": "test.txt", "content": "Hello World"}',
                    "list_dir": '{"path": "."}',
                },
                "search": {
                    "web_search": '{"query": "AI news", "num_results": 5}',
                    "news_search": '{"query": "technology"}',
                },
                "browser": {
                    "navigate": '{"url": "https://example.com"}',
                    "scrape": '{"url": "https://example.com"}',
                },
                "github": {
                    "search_repos": '{"query": "python ai"}',
                    "get_repo": '{"owner": "microsoft", "repo": "TypeScript"}',
                },
                "computer": {  # OpenClaw defaults
                    "move_mouse": '{"x": 100, "y": 200, "duration": 0.5}',
                    "click_mouse": '{"x": 100, "y": 200, "button": "left"}',
                    "type_text": '{"text": "Hello World"}',
                    "press_key": '{"key": "enter", "presses": 1}',
                    "hotkey": '{"keys": ["ctrl", "c"]}',
                    "scroll_mouse": '{"clicks": 3}',
                    "get_screen_size": "{}",
                    "get_mouse_position": "{}",
                },
                "screenshot": {  # OpenClaw defaults
                    "capture_screen": '{"region": null}',
                    "capture_window": '{"title": ""}',
                    "analyze_screen": '{"prompt": "What do you see on screen?"}',
                    "get_windows": "{}",
                },
                "shell": {  # OpenClaw defaults
                    "run_command": '{"command": "ls -la", "timeout": 30}',
                    "run_script": '{"script": "echo Hello", "language": "bash"}',
                    "get_processes": '{"filter": null}',
                    "kill_process": '{"pid": 1234, "force": false}',
                },
            }

            def update_actions(skill_name):
                actions = skill_actions.get(skill_name, [])
                default_p = (
                    default_params.get(skill_name, {}).get(actions[0], "{}")
                    if actions
                    else "{}"
                )
                return gr.update(
                    choices=actions, value=actions[0] if actions else None
                ), default_p

            def execute_skill(skill_name, action, params_json):
                try:
                    params = json.loads(params_json) if params_json else {}

                    if skill_name == "calculator":
                        from omni.skills.calculator import CalculatorSkill

                        skill = CalculatorSkill()
                        result = skill.execute(action, params)
                    elif skill_name == "file":
                        from omni.skills.file import FileSkill

                        skill = FileSkill()
                        result = skill.execute(action, params)
                    elif skill_name == "search":
                        from omni.skills.search import SearchSkill

                        skill = SearchSkill()
                        result = skill.execute(action, params)
                    elif skill_name == "browser":
                        from omni.skills.browser import BrowserSkill

                        skill = BrowserSkill()
                        result = skill.execute(action, params)
                    elif skill_name == "github":
                        from omni.skills.github import GitHubSkill

                        skill = GitHubSkill()
                        result = skill.execute(action, params)
                    elif skill_name == "computer":
                        from omni.skills.computer import ComputerSkill

                        skill = ComputerSkill()
                        result = skill.execute(action, params)
                    elif skill_name == "screenshot":
                        from omni.skills.screenshot import ScreenshotSkill

                        skill = ScreenshotSkill()
                        result = skill.execute(action, params)
                    elif skill_name == "shell":
                        from omni.skills.shell import ShellSkill

                        skill = ShellSkill()
                        result = skill.execute(action, params)
                    else:
                        return f"Unknown skill: {skill_name}"

                    return json.dumps(result, indent=2)
                except Exception as e:
                    return f"Error: {str(e)}"

            skill_choice.change(
                fn=update_actions,
                inputs=skill_choice,
                outputs=[action_choice, params_input],
            )

            execute_btn.click(
                fn=execute_skill,
                inputs=[skill_choice, action_choice, params_input],
                outputs=result_output,
            )

        with gr.Tab("Crews"):
            gr.Markdown("## Crew Management")
            gr.Markdown("View and manage department crews.")

            gr.Markdown("### Available Crews")
            crews_info = [
                {
                    "name": "Research",
                    "agents": ["Web Researcher", "Content Analyzer", "Fact Checker"],
                    "status": "Ready",
                },
                {
                    "name": "GitHub",
                    "agents": ["GitHub Researcher", "Code Analyst", "Gist Creator"],
                    "status": "Ready",
                },
                {
                    "name": "Social",
                    "agents": [
                        "Content Creator",
                        "Engagement Optimizer",
                        "Analytics Monitor",
                    ],
                    "status": "Ready",
                },
                {
                    "name": "Analysis",
                    "agents": ["Data Analyst", "Insight Generator", "Report Creator"],
                    "status": "Ready",
                },
                {
                    "name": "Writing",
                    "agents": ["Editorial Agent", "Long-form Writer", "Social Writer"],
                    "status": "Ready",
                },
                {
                    "name": "Coding",
                    "agents": [
                        "Code Generator",
                        "Refactoring Agent",
                        "Architecture Agent",
                    ],
                    "status": "Ready",
                },
                {
                    "name": "Do",
                    "agents": [
                        "Planner (Task Planning)",
                        "Executor (Computer Control)",
                        "Verifier (Task Verification)",
                    ],
                    "status": "Ready - OpenClaw Mode",
                    "description": "Executes tasks on your computer using mouse, keyboard, and shell commands",
                },
            ]

            gr.JSON(value=crews_info)

            with gr.Row():
                crew_select = gr.Dropdown(
                    label="Select Crew",
                    choices=[c["name"] for c in crews_info],
                )

            with gr.Row():
                crew_action = gr.Dropdown(
                    label="Action",
                    choices=["View Details", "Run Test"],
                )

            crew_output = gr.Textbox(label="Output", lines=5)

            def handle_crew(crew_name, action):
                if not crew_name:
                    return "Please select a crew."
                crew = next((c for c in crews_info if c["name"] == crew_name), None)
                if crew:
                    return json.dumps(crew, indent=2)
                return "Crew not found"

            gr.Button("Execute").click(
                fn=handle_crew,
                inputs=[crew_select, crew_action],
                outputs=crew_output,
            )

        with gr.Tab("System Info"):
            gr.Markdown("## System Information")

            gr.Markdown("### Status")
            gr.Markdown("- **API**: Running on port 8000")
            gr.Markdown("- **Dashboard**: Running on port 7860")
            gr.Markdown("- **Database**: PostgreSQL with pgvector")
            gr.Markdown("- **LLM**: Ollama (local)")

            gr.Markdown("### Quick Links")
            gr.Markdown("- [API Documentation](http://localhost:8000/docs)")
            gr.Markdown("- [Health Check](http://localhost:8000/health)")

            gr.Markdown("### Environment")
            env_info = {
                "PYTHONPATH": os.environ.get("PYTHONPATH", "/app"),
                "DATABASE_URL": "postgresql+asyncpg://***@postgres:5432/omni_db",
                "OLLAMA_BASE_URL": OLLAMA_URL,
                "note": "Set OLLAMA_BASE_URL env var to change (e.g., http://localhost:11434)",
            }
            gr.JSON(value=env_info)

    return dashboard


def main():
    """Run the dashboard."""
    dashboard = create_dashboard()
    dashboard.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )


if __name__ == "__main__":
    main()
