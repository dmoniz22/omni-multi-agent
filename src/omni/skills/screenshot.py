"""Screenshot skill for OMNI.

Provides screen capture capabilities for computer vision and automation.
Requires mss or pyscreenshot to be installed.
"""

import base64
import os
import tempfile
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from omni.skills.base import BaseSkill, SkillAction
from omni.core.logging import get_logger

logger = get_logger(__name__)


class CaptureScreenInput(BaseModel):
    """Input for capture_screen action."""

    region: Optional[dict] = Field(
        default=None, description="Region to capture: {x, y, width, height}"
    )
    filename: Optional[str] = Field(
        default=None, description="Filename to save screenshot (optional)"
    )


class CaptureWindowInput(BaseModel):
    """Input for capture_window action."""

    title: str = Field(
        default="",
        description="Window title substring to match (empty = focused window)",
    )


class AnalyzeScreenInput(BaseModel):
    """Input for analyze_screen action."""

    prompt: str = Field(..., description="Question about what's on the screen")
    region: Optional[dict] = Field(
        default=None, description="Region to analyze: {x, y, width, height}"
    )


class GetWindowsInput(BaseModel):
    """Input for get_windows action."""


class ScreenshotSkill(BaseSkill):
    """Screenshot capture skill for computer vision and automation.

    Provides screen capture capabilities for analyzing screen content.
    Can be combined with vision models for screen understanding.

    Actions:
        - capture_screen: Capture entire screen or region
        - capture_window: Capture specific window
        - analyze_screen: Capture and analyze with AI vision
        - get_windows: List available windows

    Usage:
        skill = ScreenshotSkill()
        result = skill.execute("capture_screen", {})
        result = skill.execute("capture_window", {"title": "Chrome"})
    """

    name = "screenshot"
    description = "Screen capture for computer vision and automation"
    version = "1.0.0"

    def __init__(self):
        """Initialize screenshot skill."""
        super().__init__()
        self._mss = None
        self._pyautogui = None

        try:
            import mss

            self._mss = mss
        except ImportError:
            logger.warning("mss not installed - screenshot skill limited")

        try:
            import pyautogui

            self._pyautogui = pyautogui
        except ImportError:
            logger.warning("pyautogui not installed - window capture limited")

    def get_actions(self) -> Dict[str, SkillAction]:
        """Get available screenshot actions."""
        return {
            "capture_screen": SkillAction(
                name="capture_screen",
                description="Capture entire screen or region",
                input_schema=CaptureScreenInput,
            ),
            "capture_window": SkillAction(
                name="capture_window",
                description="Capture specific window",
                input_schema=CaptureWindowInput,
            ),
            "analyze_screen": SkillAction(
                name="analyze_screen",
                description="Capture screen and analyze with AI vision",
                input_schema=AnalyzeScreenInput,
            ),
            "get_windows": SkillAction(
                name="get_windows",
                description="List available windows",
                input_schema=GetWindowsInput,
            ),
        }

    def execute(self, action: str, params: dict) -> dict:
        """Execute a screenshot action.

        Args:
            action: Action name
            params: Action parameters

        Returns:
            Dict with action results
        """
        if action == "capture_screen":
            return self._capture_screen(params)
        elif action == "capture_window":
            return self._capture_window(params)
        elif action == "analyze_screen":
            return self._analyze_screen(params)
        elif action == "get_windows":
            return self._get_windows(params)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _capture_screen(self, params: dict) -> dict:
        """Capture screen or region."""
        if self._mss is None:
            raise RuntimeError("mss not installed. Run: pip install mss")

        validated = CaptureScreenInput.model_validate(params)

        with self._mss.mss() as sct:
            if validated.region:
                region = validated.region
                monitor = {
                    "left": region.get("x", 0),
                    "top": region.get("y", 0),
                    "width": region.get("width", 1920),
                    "height": region.get("height", 1080),
                }
            else:
                monitor = sct.monitors[1]

            screenshot = sct.grab(monitor)

            if validated.filename:
                output_path = validated.filename
            else:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                    output_path = f.name

            self._mss.tools.to_png(screenshot.rgb, screenshot.size, output=output_path)

            with open(output_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()

            if not validated.filename:
                os.unlink(output_path)

            return {
                "success": True,
                "width": screenshot.width,
                "height": screenshot.height,
                "saved_to": validated.filename,
                "message": f"Captured screen: {screenshot.width}x{screenshot.height}",
            }

    def _capture_window(self, params: dict) -> dict:
        """Capture specific window."""
        validated = CaptureWindowInput.model_validate(params)

        if self._pyautogui is None:
            raise RuntimeError("pyautogui not installed. Run: pip install pyautogui")

        if self._mss is None:
            raise RuntimeError("mss not installed. Run: pip install mss")

        try:
            import pygetwindow as gw

            windows = (
                gw.getWindowsWithTitle(validated.title)
                if validated.title
                else [gw.getActiveWindow()]
            )

            if not windows:
                return {
                    "success": False,
                    "error": f"No window found matching: {validated.title or 'focused window'}",
                }

            window = windows[0]

            with self._mss.mss() as sct:
                monitor = {
                    "left": window.left,
                    "top": window.top,
                    "width": window.width,
                    "height": window.height,
                }
                screenshot = sct.grab(monitor)

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                    output_path = f.name

                self._mss.tools.to_png(
                    screenshot.rgb, screenshot.size, output=output_path
                )

                with open(output_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode()

                os.unlink(output_path)

                return {
                    "success": True,
                    "window_title": window.title,
                    "width": screenshot.width,
                    "height": screenshot.height,
                    "message": f"Captured window: {window.title}",
                }
        except ImportError:
            raise RuntimeError(
                "pygetwindow not installed. Run: pip install pygetwindow"
            )

    def _analyze_screen(self, params: dict) -> dict:
        """Capture and analyze screen with AI."""
        validated = AnalyzeScreenInput.model_validate(params)

        screen_result = self._capture_screen({"region": validated.region})

        return {
            "success": True,
            "prompt": validated.prompt,
            "screen_info": {
                "width": screen_result.get("width"),
                "height": screen_result.get("height"),
            },
            "message": f"Screen captured. Use a vision model to analyze: {validated.prompt}",
            "note": "Connect to a vision model (like llava) to analyze screen content",
        }

    def _get_windows(self, params: dict) -> dict:
        """List available windows."""
        try:
            import pygetwindow as gw

            windows = gw.getAllWindows()

            window_list = []
            for w in windows:
                if w.title.strip():
                    window_list.append(
                        {
                            "title": w.title,
                            "size": f"{w.width}x{w.height}",
                            "position": f"({w.left}, {w.top})",
                        }
                    )

            return {
                "success": True,
                "windows": window_list,
                "count": len(window_list),
            }
        except ImportError:
            raise RuntimeError(
                "pygetwindow not installed. Run: pip install pygetwindow"
            )

    def health_check(self) -> bool:
        """Verify screenshot skill is operational."""
        if self._mss is None:
            return False
        try:
            with self._mss.mss() as sct:
                sct.monitors[1]
            return True
        except Exception:
            return False
