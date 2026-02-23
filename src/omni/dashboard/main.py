"""Gradio dashboard for OMNI."""

import gradio as gr
from typing import Optional

from omni.core.logging import get_logger
from omni.skills.registry import get_skill_registry

logger = get_logger(__name__)


def create_dashboard() -> gr.Blocks:
    """Create the OMNI Gradio dashboard.

    Returns:
        Gradio Blocks application
    """
    skill_registry = get_skill_registry()

    with gr.Blocks(title="OMNI Dashboard") as dashboard:
        gr.Markdown("# OMNI Multi-Agent Orchestration System")
        gr.Markdown("Manage tasks, monitor crews, and interact with skills.")

        with gr.Tab("Tasks"):
            gr.Markdown("## Task Management")
            with gr.Row():
                task_input = gr.Textbox(
                    label="Task",
                    placeholder="Enter your task...",
                    lines=3,
                )
            with gr.Row():
                submit_btn = gr.Button("Submit Task", variant="primary")
            task_output = gr.Textbox(label="Result", lines=5)

            submit_btn.click(
                fn=lambda x: f"Task submitted: {x[:50]}...",
                inputs=task_input,
                outputs=task_output,
            )

        with gr.Tab("Skills"):
            gr.Markdown("## Available Skills")
            skills = skill_registry.list_available()

            skills_list = (
                "\n".join(
                    [
                        f"- **{s.name}**: {s.description} (actions: {', '.join(s.actions)})"
                        for s in skills
                    ]
                )
                or "No skills registered"
            )

            gr.Markdown(skills_list)

            gr.Markdown("### Test a Skill")
            with gr.Row():
                skill_select = gr.Dropdown(
                    label="Select Skill",
                    choices=[s.name for s in skills],
                )
                action_select = gr.Dropdown(
                    label="Select Action",
                    choices=[],
                )
            with gr.Row():
                params_input = gr.Textbox(
                    label="Parameters (JSON)",
                    placeholder='{"param": "value"}',
                )
            with gr.Row():
                test_btn = gr.Button("Execute", variant="primary")
            test_output = gr.Textbox(label="Result", lines=5)

            def update_actions(skill_name: str):
                skill = skill_registry.get(skill_name)
                if skill:
                    return gr.update(choices=list(skill.get_actions().keys()))
                return gr.update(choices=[])

            skill_select.change(
                fn=update_actions,
                inputs=skill_select,
                outputs=action_select,
            )

            def execute_skill(skill_name: str, action: str, params_json: str):
                try:
                    import json

                    params = json.loads(params_json) if params_json else {}
                    result = skill_registry.execute(skill_name, action, params)
                    return str(result)
                except Exception as e:
                    return f"Error: {str(e)}"

            test_btn.click(
                fn=execute_skill,
                inputs=[skill_select, action_select, params_input],
                outputs=test_output,
            )

        with gr.Tab("Crews"):
            gr.Markdown("## Crew Status")
            gr.Markdown("Crew management interface - coming soon!")

        with gr.Tab("Settings"):
            gr.Markdown("## System Settings")
            gr.Markdown(
                f"**Registered Skills**: {len(skill_registry.list_available())}"
            )
            gr.Markdown("Configuration options - coming soon!")

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
