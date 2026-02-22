"""File skill for OMNI.

Provides file operations: read, write, list directory contents.
Sandboxed to a configurable workspace directory.
"""

import os
from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel, Field

from omni.skills.base import BaseSkill, SkillAction


class FileReadInput(BaseModel):
    """Input for file read action."""

    path: str = Field(..., description="Path to the file to read")


class FileReadOutput(BaseModel):
    """Output from file read action."""

    content: str = Field(..., description="File contents")
    size: int = Field(..., description="File size in bytes")
    path: str = Field(..., description="Path to the file")


class FileWriteInput(BaseModel):
    """Input for file write action."""

    path: str = Field(..., description="Path to write to")
    content: str = Field(..., description="Content to write")


class FileWriteOutput(BaseModel):
    """Output from file write action."""

    success: bool = Field(..., description="Whether write succeeded")
    path: str = Field(..., description="Path to the file")
    bytes_written: int = Field(..., description="Number of bytes written")


class FileListDirInput(BaseModel):
    """Input for list directory action."""

    path: str = Field(..., description="Path to directory")


class FileEntry(BaseModel):
    """A file or directory entry."""

    name: str = Field(..., description="File/directory name")
    is_file: bool = Field(..., description="Whether this is a file")
    is_dir: bool = Field(..., description="Whether this is a directory")
    size: int = Field(default=0, description="File size (0 for directories)")


class FileListDirOutput(BaseModel):
    """Output from list directory action."""

    entries: list[FileEntry] = Field(..., description="List of entries")
    path: str = Field(..., description="Path to the directory")


class FileSkill(BaseSkill):
    """File operations skill with sandboxed workspace access.

    Provides read, write, and list operations within a configurable
    workspace directory. Path traversal prevention is enforced.

    Actions:
        - read: Read file contents
        - write: Write content to file
        - list_dir: List directory contents

    Usage:
        skill = FileSkill()
        result = skill.execute("read", {"path": "/workspace/myfile.txt"})
    """

    name = "file"
    description = "File operations: read, write, list directory contents"
    version = "1.0.0"

    def __init__(self, workspace: str = "/tmp/omni_workspace"):
        """Initialize file skill with workspace directory.

        Args:
            workspace: Root directory for file operations (default: /tmp/omni_workspace)
        """
        super().__init__()
        self._workspace = Path(workspace).resolve()
        self._workspace.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, path: str) -> Path:
        """Resolve and validate a path within workspace.

        Args:
            path: User-provided path

        Returns:
            Resolved Path within workspace

        Raises:
            ValueError: If path attempts to escape workspace
        """
        resolved = (self._workspace / path).resolve()

        if not str(resolved).startswith(str(self._workspace)):
            raise ValueError(f"Path outside workspace: {path}")

        return resolved

    def get_actions(self) -> Dict[str, SkillAction]:
        """Get available file actions."""
        return {
            "read": SkillAction(
                name="read",
                description="Read contents of a file",
                input_schema=FileReadInput,
                output_schema=FileReadOutput,
            ),
            "write": SkillAction(
                name="write",
                description="Write content to a file",
                input_schema=FileWriteInput,
                output_schema=FileWriteOutput,
            ),
            "list_dir": SkillAction(
                name="list_dir",
                description="List contents of a directory",
                input_schema=FileListDirInput,
                output_schema=FileListDirOutput,
            ),
        }

    def execute(self, action: str, params: dict) -> dict:
        """Execute a file action.

        Args:
            action: Action name (read, write, list_dir)
            params: Action parameters

        Returns:
            Dict with action results

        Raises:
            ValueError: If action is unknown
            FileNotFoundError: If file/directory not found
            PermissionError: If access denied
        """
        if action == "read":
            return self._read(params)
        elif action == "write":
            return self._write(params)
        elif action == "list_dir":
            return self._list_dir(params)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _read(self, params: dict) -> dict:
        """Read file contents."""
        validated = FileReadInput.model_validate(params)
        path = self._resolve_path(validated.path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {validated.path}")

        if not path.is_file():
            raise ValueError(f"Not a file: {validated.path}")

        content = path.read_text(encoding="utf-8")
        size = path.stat().st_size

        return {
            "content": content,
            "size": size,
            "path": str(path.relative_to(self._workspace)),
        }

    def _write(self, params: dict) -> dict:
        """Write content to file."""
        validated = FileWriteInput.model_validate(params)
        path = self._resolve_path(validated.path)

        path.parent.mkdir(parents=True, exist_ok=True)

        bytes_written = path.write_text(validated.content, encoding="utf-8")

        return {
            "success": True,
            "path": str(path.relative_to(self._workspace)),
            "bytes_written": bytes_written,
        }

    def _list_dir(self, params: dict) -> dict:
        """List directory contents."""
        validated = FileListDirInput.model_validate(params)
        path = self._resolve_path(validated.path)

        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {validated.path}")

        if not path.is_dir():
            raise ValueError(f"Not a directory: {validated.path}")

        entries = []
        for entry in sorted(path.iterdir()):
            stat = entry.stat()
            entries.append(
                {
                    "name": entry.name,
                    "is_file": entry.is_file(),
                    "is_dir": entry.is_dir(),
                    "size": stat.st_size if entry.is_file() else 0,
                }
            )

        return {
            "entries": entries,
            "path": str(path.relative_to(self._workspace)),
        }

    def health_check(self) -> bool:
        """Verify workspace is accessible."""
        try:
            return self._workspace.exists() and self._workspace.is_dir()
        except Exception:
            return False
