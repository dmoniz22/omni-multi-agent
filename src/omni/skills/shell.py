"""Shell skill for OMNI.

Provides shell command execution for automation.
WARNING: Execute with caution - can run any command on the system.
"""

import os
import shlex
import subprocess
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from omni.skills.base import BaseSkill, SkillAction
from omni.core.logging import get_logger

logger = get_logger(__name__)


class RunCommandInput(BaseModel):
    """Input for run_command action."""

    command: str = Field(..., description="Shell command to execute")
    timeout: int = Field(default=30, description="Timeout in seconds")
    cwd: Optional[str] = Field(default=None, description="Working directory")
    env: Optional[dict] = Field(default=None, description="Environment variables")


class RunScriptInput(BaseModel):
    """Input for run_script action."""

    script: str = Field(..., description="Script content to execute")
    language: str = Field(
        default="bash", description="Script language: bash, python, node"
    )
    timeout: int = Field(default=30, description="Timeout in seconds")


class GetProcessesInput(BaseModel):
    """Input for get_processes action."""

    filter: Optional[str] = Field(default=None, description="Filter by process name")


class KillProcessInput(BaseModel):
    """Input for kill_process action."""

    pid: int = Field(..., description="Process ID to kill")
    force: bool = Field(default=False, description="Force kill (SIGKILL)")


class ShellSkill(BaseSkill):
    """Shell command execution skill for automation.

    Provides shell command execution capabilities.
    WARNING: This skill can execute arbitrary commands - use with caution.

    Actions:
        - run_command: Execute shell command
        - run_script: Execute script (bash/python/node)
        - get_processes: List running processes
        - kill_process: Kill a process

    Usage:
        skill = ShellSkill()
        result = skill.execute("run_command", {"command": "ls -la"})
        result = skill.execute("run_script", {"script": "echo 'Hello'", "language": "bash"})
    """

    name = "shell"
    description = "Shell command execution for automation"
    version = "1.0.0"

    ALLOWED_COMMANDS = {
        "ls",
        "cd",
        "pwd",
        "cat",
        "grep",
        "find",
        "echo",
        "mkdir",
        "rm",
        "cp",
        "mv",
        "touch",
        "chmod",
        "chown",
        "curl",
        "wget",
        "git",
        "npm",
        "pip",
        "python",
        "node",
        "yarn",
        "docker",
        "kubectl",
        "terraform",
        "ansible",
    }

    BLOCKED_COMMANDS = {
        "rm -rf /",
        "mkfs",
        "dd if=",
        ">:",
        "> /dev/sd",
        "chmod 777 /",
    }

    def __init__(self):
        """Initialize shell skill."""
        super().__init__()

    def get_actions(self) -> Dict[str, SkillAction]:
        """Get available shell actions."""
        return {
            "run_command": SkillAction(
                name="run_command",
                description="Execute a shell command",
                input_schema=RunCommandInput,
            ),
            "run_script": SkillAction(
                name="run_script",
                description="Execute a script (bash/python/node)",
                input_schema=RunScriptInput,
            ),
            "get_processes": SkillAction(
                name="get_processes",
                description="List running processes",
                input_schema=GetProcessesInput,
            ),
            "kill_process": SkillAction(
                name="kill_process",
                description="Kill a process by PID",
                input_schema=KillProcessInput,
            ),
        }

    def execute(self, action: str, params: dict) -> dict:
        """Execute a shell action.

        Args:
            action: Action name
            params: Action parameters

        Returns:
            Dict with action results
        """
        if action == "run_command":
            return self._run_command(params)
        elif action == "run_script":
            return self._run_script(params)
        elif action == "get_processes":
            return self._get_processes(params)
        elif action == "kill_process":
            return self._kill_process(params)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _run_command(self, params: dict) -> dict:
        """Execute shell command."""
        validated = RunCommandInput.model_validate(params)

        command = validated.command.strip()

        for blocked in self.BLOCKED_COMMANDS:
            if blocked in command:
                logger.warning("Blocked command attempted", command=command[:100])
                return {
                    "success": False,
                    "error": f"Command blocked: contains dangerous pattern '{blocked}'",
                }

        try:
            env = os.environ.copy()
            if validated.env:
                env.update(validated.env)

            # Use shlex.split to safely parse command and avoid shell=True
            try:
                cmd_parts = shlex.split(command)
            except ValueError:
                # Fall back to shell=True for commands with complex shell syntax
                cmd_parts = command
                use_shell = True
            else:
                use_shell = False

            result = subprocess.run(
                cmd_parts,
                shell=use_shell,
                capture_output=True,
                text=True,
                timeout=validated.timeout,
                cwd=validated.cwd,
                env=env,
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {validated.timeout} seconds",
                "command": command,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command,
            }

    def _run_script(self, params: dict) -> dict:
        """Execute script safely by writing to a temp file."""
        validated = RunScriptInput.model_validate(params)

        language = validated.language.lower()
        import tempfile

        lang_extensions = {"bash": ".sh", "python": ".py", "node": ".js"}
        lang_interpreters = {"bash": "bash", "python": "python3", "node": "node"}

        if language not in lang_extensions:
            return {
                "success": False,
                "error": f"Unsupported language: {language}. Supported: bash, python, node",
            }

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=lang_extensions[language],
                delete=False,
            ) as tmp:
                tmp.write(validated.script)
                tmp_path = tmp.name

            try:
                result = subprocess.run(
                    [lang_interpreters[language], tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=validated.timeout,
                )

                return {
                    "success": result.returncode == 0,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "language": language,
                }
            finally:
                os.unlink(tmp_path)

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Script timed out after {validated.timeout} seconds",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _get_processes(self, params: dict) -> dict:
        """List running processes."""
        validated = GetProcessesInput.model_validate(params)

        try:
            if validated.filter:
                # Sanitize filter to prevent shell injection
                safe_filter = "".join(
                    c for c in validated.filter if c.isalnum() or c in "-_."
                )
                if not safe_filter:
                    return {
                        "success": False,
                        "error": "Invalid filter: must contain alphanumeric characters",
                    }
                result = subprocess.run(
                    ["ps", "aux"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                # Filter in Python instead of shell
            lines = result_stdout.strip().split("\n")
                filtered_lines = [lines[0]] + [l for l in lines[1:] if safe_filter in l]
                result_stdout = "\n".join(filtered_lines)
            else:
                result = subprocess.run(
                    ["ps", "aux"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                result_stdout = result.stdout

            lines = result.stdout.strip().split("\n")
            processes = []

            for line in lines[1:]:
                if line.strip():
                    parts = line.split(None, 10)
                    if len(parts) >= 11:
                        processes.append(
                            {
                                "user": parts[0],
                                "pid": parts[1],
                                "cpu": parts[2],
                                "mem": parts[3],
                                "command": parts[10],
                            }
                        )

            return {
                "success": True,
                "processes": processes[:50],
                "count": len(processes),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _kill_process(self, params: dict) -> dict:
        """Kill a process."""
        validated = KillProcessInput.model_validate(params)

        try:
            signal = "-9" if validated.force else "-15"
            result = subprocess.run(
                ["kill", signal, str(validated.pid)],
                capture_output=True,
                text=True,
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "pid": validated.pid,
                "force": validated.force,
                "message": f"Killed process {validated.pid}"
                if result.returncode == 0
                else f"Failed to kill: {result.stderr}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def health_check(self) -> bool:
        """Verify shell skill is operational."""
        try:
            result = subprocess.run(
                ["echo", "test"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False
