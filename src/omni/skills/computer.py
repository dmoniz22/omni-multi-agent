"""Computer skill for OMNI.

Provides mouse and keyboard control for computer automation.
Requires pyautogui to be installed.
"""

import time
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from omni.skills.base import BaseSkill, SkillAction
from omni.core.logging import get_logger

logger = get_logger(__name__)


class MoveMouseInput(BaseModel):
    """Input for move_mouse action."""

    x: int = Field(..., description="X coordinate to move to")
    y: int = Field(..., description="Y coordinate to move to")
    duration: float = Field(default=0.5, description="Movement duration in seconds")


class ClickMouseInput(BaseModel):
    """Input for click_mouse action."""

    x: Optional[int] = Field(default=None, description="X coordinate (optional)")
    y: Optional[int] = Field(default=None, description="Y coordinate (optional)")
    button: str = Field(default="left", description="Mouse button: left, right, middle")
    clicks: int = Field(default=1, description="Number of clicks")


class TypeTextInput(BaseModel):
    """Input for type_text action."""

    text: str = Field(..., description="Text to type")
    interval: float = Field(default=0.05, description="Interval between keystrokes")


class PressKeyInput(BaseModel):
    """Input for press_key action."""

    key: str = Field(..., description="Key to press (e.g., enter, ctrl, alt)")
    presses: int = Field(default=1, description="Number of times to press")


class HotkeyInput(BaseModel):
    """Input for hotkey action."""

    keys: list[str] = Field(
        ..., description="Keys to press together (e.g., ['ctrl', 'c'])"
    )


class ScrollMouseInput(BaseModel):
    """Input for scroll_mouse action."""

    x: Optional[int] = Field(default=None, description="X coordinate (optional)")
    y: Optional[int] = Field(default=None, description="Y coordinate (optional)")
    clicks: int = Field(
        default=3, description="Number of scroll clicks (positive=up, negative=down)"
    )


class GetScreenSizeInput(BaseModel):
    """Input for get_screen_size action."""


class GetMousePositionInput(BaseModel):
    """Input for get_mouse_position action."""


class ComputerSkill(BaseSkill):
    """Computer control skill for mouse and keyboard automation.

    Provides low-level computer control for automating tasks.
    This is the foundation for building OpenClaw-like functionality.

    Actions:
        - move_mouse: Move mouse cursor to coordinates
        - click_mouse: Click at coordinates or current position
        - type_text: Type text using keyboard
        - press_key: Press a single key
        - hotkey: Press key combination
        - scroll_mouse: Scroll up/down
        - get_screen_size: Get screen dimensions
        - get_mouse_position: Get current mouse coordinates

    Usage:
        skill = ComputerSkill()
        skill.execute("move_mouse", {"x": 100, "y": 200})
        skill.execute("click_mouse", {"x": 100, "y": 200})
        skill.execute("type_text", {"text": "Hello World"})
        skill.execute("hotkey", {"keys": ["ctrl", "c"]})
    """

    name = "computer"
    description = "Mouse and keyboard control for computer automation"
    version = "1.0.0"

    def __init__(self):
        """Initialize computer skill."""
        super().__init__()
        try:
            import pyautogui

            self._pyautogui = pyautogui
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.1
        except ImportError:
            self._pyautogui = None
            logger.warning("pyautogui not installed - computer skill disabled")

    def get_actions(self) -> Dict[str, SkillAction]:
        """Get available computer control actions."""
        return {
            "move_mouse": SkillAction(
                name="move_mouse",
                description="Move mouse cursor to specified coordinates",
                input_schema=MoveMouseInput,
            ),
            "click_mouse": SkillAction(
                name="click_mouse",
                description="Click mouse button at coordinates",
                input_schema=ClickMouseInput,
            ),
            "type_text": SkillAction(
                name="type_text",
                description="Type text using keyboard",
                input_schema=TypeTextInput,
            ),
            "press_key": SkillAction(
                name="press_key",
                description="Press a single key",
                input_schema=PressKeyInput,
            ),
            "hotkey": SkillAction(
                name="hotkey",
                description="Press key combination (e.g., ctrl+c)",
                input_schema=HotkeyInput,
            ),
            "scroll_mouse": SkillAction(
                name="scroll_mouse",
                description="Scroll mouse wheel",
                input_schema=ScrollMouseInput,
            ),
            "get_screen_size": SkillAction(
                name="get_screen_size",
                description="Get screen dimensions",
                input_schema=GetScreenSizeInput,
            ),
            "get_mouse_position": SkillAction(
                name="get_mouse_position",
                description="Get current mouse coordinates",
                input_schema=GetMousePositionInput,
            ),
        }

    def execute(self, action: str, params: dict) -> dict:
        """Execute a computer control action.

        Args:
            action: Action name
            params: Action parameters

        Returns:
            Dict with action results
        """
        if self._pyautogui is None:
            raise RuntimeError("pyautogui not installed. Run: pip install pyautogui")

        if action == "move_mouse":
            return self._move_mouse(params)
        elif action == "click_mouse":
            return self._click_mouse(params)
        elif action == "type_text":
            return self._type_text(params)
        elif action == "press_key":
            return self._press_key(params)
        elif action == "hotkey":
            return self._hotkey(params)
        elif action == "scroll_mouse":
            return self._scroll_mouse(params)
        elif action == "get_screen_size":
            return self._get_screen_size(params)
        elif action == "get_mouse_position":
            return self._get_mouse_position(params)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _move_mouse(self, params: dict) -> dict:
        """Move mouse to coordinates."""
        validated = MoveMouseInput.model_validate(params)
        self._pyautogui.moveTo(validated.x, validated.y, duration=validated.duration)
        return {
            "success": True,
            "x": validated.x,
            "y": validated.y,
            "message": f"Moved mouse to ({validated.x}, {validated.y})",
        }

    def _click_mouse(self, params: dict) -> dict:
        """Click mouse button."""
        validated = ClickMouseInput.model_validate(params)

        if validated.x is not None and validated.y is not None:
            self._pyautogui.click(
                x=validated.x,
                y=validated.y,
                clicks=validated.clicks,
                button=validated.button,
            )
        else:
            self._pyautogui.click(clicks=validated.clicks, button=validated.button)

        return {
            "success": True,
            "x": validated.x,
            "y": validated.y,
            "button": validated.button,
            "clicks": validated.clicks,
            "message": f"Clicked {validated.button} button",
        }

    def _type_text(self, params: dict) -> dict:
        """Type text."""
        validated = TypeTextInput.model_validate(params)
        self._pyautogui.write(validated.text, interval=validated.interval)
        return {
            "success": True,
            "text": validated.text,
            "message": f"Typed: {validated.text}",
        }

    def _press_key(self, params: dict) -> dict:
        """Press a key."""
        validated = PressKeyInput.model_validate(params)
        for _ in range(validated.presses):
            self._pyautogui.press(validated.key)
        return {
            "success": True,
            "key": validated.key,
            "presses": validated.presses,
            "message": f"Pressed {validated.key} {validated.presses} time(s)",
        }

    def _hotkey(self, params: dict) -> dict:
        """Press key combination."""
        validated = HotkeyInput.model_validate(params)
        self._pyautogui.hotkey(*validated.keys)
        return {
            "success": True,
            "keys": validated.keys,
            "message": f"Pressed hotkey: {'+'.join(validated.keys)}",
        }

    def _scroll_mouse(self, params: dict) -> dict:
        """Scroll mouse wheel."""
        validated = ScrollMouseInput.model_validate(params)

        if validated.x is not None and validated.y is not None:
            self._pyautogui.click(x=validated.x, y=validated.y)
            time.sleep(0.1)

        self._pyautogui.scroll(validated.clicks)

        return {
            "success": True,
            "clicks": validated.clicks,
            "message": f"Scrolled {validated.clicks} clicks",
        }

    def _get_screen_size(self, params: dict) -> dict:
        """Get screen dimensions."""
        size = self._pyautogui.size()
        return {
            "success": True,
            "width": size.width,
            "height": size.height,
            "message": f"Screen size: {size.width}x{size.height}",
        }

    def _get_mouse_position(self, params: dict) -> dict:
        """Get current mouse position."""
        pos = self._pyautogui.position()
        return {
            "success": True,
            "x": pos.x,
            "y": pos.y,
            "message": f"Mouse at ({pos.x}, {pos.y})",
        }

    def health_check(self) -> bool:
        """Verify computer skill is operational."""
        if self._pyautogui is None:
            return False
        try:
            self._pyautogui.size()
            return True
        except Exception:
            return False
