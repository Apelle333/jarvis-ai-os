"""
JARVIS AI Operating System - Automation Tool
Handles GUI automation, mouse/keyboard control, and task automation
"""

import asyncio
import logging
import time
import pyautogui
import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import platform
import subprocess
import os
import shutil
import psutil
from PIL import ImageGrab

logger = logging.getLogger(__name__)

# Avoid console windows when JARVIS (pythonw) spawns commands on Windows.
_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class AutomationTool:
    """
    Automation Tool - Handles GUI automation and task automation
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        self.screen_width, self.screen_height = pyautogui.size()
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.1  # Default pause between actions

        # Safety settings
        self.max_duration = 300  # Maximum automation duration in seconds
        self.safety_enabled = True

        # Platform-specific settings
        self.platform = platform.system().lower()

    async def initialize(self):
        """Initialize the automation tool"""
        try:
            self.logger.info("Initializing Automation Tool...")
            # Test basic functionality
            await self.get_screen_size()
            self.is_initialized = True
            self.logger.info("Automation Tool initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Automation Tool: {e}")
            raise

    async def get_screen_size(self) -> Dict[str, int]:
        """Get screen dimensions"""
        if not self.is_initialized:
            await self.initialize()

        width, height = pyautogui.size()
        return {
            "width": width,
            "height": height
        }

    async def take_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> bytes:
        """
        Take a screenshot

        Args:
            region: Optional tuple (x, y, width, height) for region to capture

        Returns:
            Screenshot as PNG bytes
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            if region:
                x, y, w, h = region
                screenshot = pyautogui.screenshot(region=(x, y, w, h))
            else:
                screenshot = pyautogui.screenshot()

            # Convert to bytes
            import io
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            self.logger.info(f"Screenshot taken: {len(img_byte_arr)} bytes")
            return img_byte_arr

        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            raise

    async def move_mouse(self, x: int, y: int, duration: float = 0.5) -> Dict[str, Any]:
        """
        Move mouse to coordinates

        Args:
            x: X coordinate
            y: Y coordinate
            duration: Time to take for movement (seconds)

        Returns:
            Result dictionary
        """
        if not self.is_initialized:
            await self.initialize()

        # Safety check
        if self.safety_enabled:
            if not (0 <= x <= self.screen_width and 0 <= y <= self.screen_height):
                return {
                    "success": False,
                    "error": f"Coordinates ({x}, {y}) out of screen bounds ({self.screen_width}x{self.screen_height})"
                }

        try:
            pyautogui.moveTo(x, y, duration=duration)
            self.logger.info(f"Mouse moved to ({x}, {y})")
            return {
                "success": True,
                "position": (x, y),
                "duration": duration
            }
        except Exception as e:
            self.logger.error(f"Error moving mouse: {e}")
            return {
                "success": False,
                "error": f"Failed to move mouse: {str(e)}"
            }

    async def click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
        clicks: int = 1,
        interval: float = 0.0
    ) -> Dict[str, Any]:
        """
        Click mouse button

        Args:
            x: X coordinate (optional, uses current position if not provided)
            y: Y coordinate (optional, uses current position if not provided)
            button: Mouse button ('left', 'right', 'middle')
            clicks: Number of clicks
            interval: Time between clicks

        Returns:
            Result dictionary
        """
        if not self.is_initialized:
            await self.initialize()

        # Get current position if not provided
        if x is None or y is None:
            current_x, current_y = pyautogui.position()
            if x is None:
                x = current_x
            if y is None:
                y = current_y

        # Safety check
        if self.safety_enabled:
            if not (0 <= x <= self.screen_width and 0 <= y <= self.screen_height):
                return {
                    "success": False,
                    "error": f"Coordinates ({x}, {y}) out of screen bounds ({self.screen_width}x{self.screen_height})"
                }

        try:
            pyautogui.click(x=x, y=y, button=button, clicks=clicks, interval=interval)
            self.logger.info(f"Clicked at ({x}, {y}) with {button} button ({clicks} clicks)")
            return {
                "success": True,
                "position": (x, y),
                "button": button,
                "clicks": clicks,
                "interval": interval
            }
        except Exception as e:
            self.logger.error(f"Error clicking: {e}")
            return {
                "success": False,
                "error": f"Failed to click: {str(e)}"
            }

    async def double_click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left"
    ) -> Dict[str, Any]:
        """
        Double click mouse button

        Args:
            x: X coordinate (optional)
            y: Y coordinate (optional)
            button: Mouse button ('left', 'right', 'middle')

        Returns:
            Result dictionary
        """
        return await self.click(x=x, y=y, button=button, clicks=2, interval=0.1)

    async def right_click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Right click mouse button

        Args:
            x: X coordinate (optional)
            y: Y coordinate (optional)

        Returns:
            Result dictionary
        """
        return await self.click(x=x, y=y, button="right")

    async def drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: float = 0.5,
        button: str = "left"
    ) -> Dict[str, Any]:
        """
        Drag mouse from start to end position

        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            duration: Time to take for drag (seconds)
            button: Mouse button to use

        Returns:
            Result dictionary
        """
        if not self.is_initialized:
            await self.initialize()

        # Safety check
        if self.safety_enabled:
            coords = [(start_x, start_y), (end_x, end_y)]
            for x, y in coords:
                if not (0 <= x <= self.screen_width and 0 <= y <= self.screen_height):
                    return {
                        "success": False,
                        "error": f"Coordinates ({x}, {y}) out of screen bounds ({self.screen_width}x{self.screen_height})"
                    }

        try:
            pyautogui.moveTo(start_x, start_y)
            pyautogui.dragTo(end_x, end_y, duration=duration, button=button)
            self.logger.info(f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})")
            return {
                "success": True,
                "start": (start_x, start_y),
                "end": (end_x, end_y),
                "duration": duration,
                "button": button
            }
        except Exception as e:
            self.logger.error(f"Error dragging: {e}")
            return {
                "success": False,
                "error": f"Failed to drag: {str(e)}"
            }

    async def type_text(self, text: str, interval: float = 0.01) -> Dict[str, Any]:
        """
        Type text

        Args:
            text: Text to type
            interval: Time between keystrokes (seconds)

        Returns:
            Result dictionary
        """
        if not self.is_initialized:
            await self.initialize()

        if not text:
            return {
                "success": False,
                "error": "Text cannot be empty"
            }

        try:
            pyautogui.typewrite(text, interval=interval)
            self.logger.info(f"Typed text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            return {
                "success": True,
                "text": text,
                "length": len(text),
                "interval": interval
            }
        except Exception as e:
            self.logger.error(f"Error typing text: {e}")
            return {
                "success": False,
                "error": f"Failed to type text: {str(e)}"
            }

    async def press_key(self, key: str) -> Dict[str, Any]:
        """
        Press a single key

        Args:
            key: Key to press (e.g., 'enter', 'esc', 'space', 'a', 'ctrl', etc.)

        Returns:
            Result dictionary
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            pyautogui.press(key)
            self.logger.info(f"Pressed key: {key}")
            return {
                "success": True,
                "key": key
            }
        except Exception as e:
            self.logger.error(f"Error pressing key {key}: {e}")
            return {
                "success": False,
                "error": f"Failed to press key: {str(e)}"
            }

    async def hotkey(self, *keys) -> Dict[str, Any]:
        """
        Press a combination of keys (hotkey)

        Args:
            *keys: Keys to press together (e.g., 'ctrl', 'c' for Ctrl+C)

        Returns:
            Result dictionary
        """
        if not self.is_initialized:
            await self.initialize()

        if not keys:
            return {
                "success": False,
                "error": "No keys provided"
            }

        try:
            pyautogui.hotkey(*keys)
            key_str = "+".join(keys)
            self.logger.info(f"Pressed hotkey: {key_str}")
            return {
                "success": True,
                "keys": keys,
                "key_string": key_str
            }
        except Exception as e:
            self.logger.error(f"Error pressing hotkey {keys}: {e}")
            return {
                "success": False,
                "error": f"Failed to press hotkey: {str(e)}"
            }

    async def scroll(
        self,
        clicks: int,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Scroll mouse wheel

        Args:
            clicks: Number of scroll clicks (positive = up, negative = down)
            x: X coordinate (optional, uses current position)
            y: Y coordinate (optional, uses current position)

        Returns:
            Result dictionary
        """
        if not self.is_initialized:
            await self.initialize()

        # Get current position if not provided
        if x is None or y is None:
            current_x, current_y = pyautogui.position()
            if x is None:
                x = current_x
            if y is None:
                y = current_y

        # Safety check
        if self.safety_enabled:
            if not (0 <= x <= self.screen_width and 0 <= y <= self.screen_height):
                return {
                    "success": False,
                    "error": f"Coordinates ({x}, {y}) out of screen bounds ({self.screen_width}x{self.screen_height})"
                }

        try:
            pyautogui.scroll(clicks, x=x, y=y)
            self.logger.info(f"Scrolled {clicks} clicks at ({x}, {y})")
            return {
                "success": True,
                "position": (x, y),
                "clicks": clicks
            }
        except Exception as e:
            self.logger.error(f"Error scrolling: {e}")
            return {
                "success": False,
                "error": f"Failed to scroll: {str(e)}"
            }

    async def find_image_on_screen(
        self,
        template_path: str,
        confidence: float = 0.8,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """
        Find an image on the screen using template matching

        Args:
            template_path: Path to template image
            confidence: Confidence threshold (0.0 to 1.0)
            region: Optional region to search (x, y, width, height)

        Returns:
            Result dictionary with match location
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            if not os.path.exists(template_path):
                return {
                    "success": False,
                    "error": f"Template file not found: {template_path}"
                }

            # Take screenshot
            screenshot_bytes = await self.take_screenshot(region)
            # Convert to OpenCV format
            import io
            from PIL import Image
            image = Image.open(io.BytesIO(screenshot_bytes))
            img_np = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Load template
            template = cv2.imread(template_path)
            if template is None:
                return {
                    "success": False,
                    "error": f"Could not load template image: {template_path}"
                }

            # Template matching
            result = cv2.matchTemplate(img_np, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= confidence:
                # Get center of match
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2

                self.logger.info(f"Found template match at ({center_x}, {center_y}) with confidence {max_val:.2f}")
                return {
                    "success": True,
                    "found": True,
                    "confidence": float(max_val),
                    "position": (center_x, center_y),
                    "top_left": max_loc,
                    "template_size": (w, h)
                }
            else:
                self.logger.info(f"No template match found above threshold {confidence} (best: {max_val:.2f})")
                return {
                    "success": True,
                    "found": False,
                    "confidence": float(max_val),
                    "best_match": max_loc if max_val > 0 else None
                }

        except Exception as e:
            self.logger.error(f"Error finding image on screen: {e}")
            return {
                "success": False,
                "error": f"Failed to find image: {str(e)}"
            }

    async def wait_for_image(
        self,
        template_path: str,
        timeout: float = 30.0,
        confidence: float = 0.8,
        interval: float = 0.5,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """
        Wait for an image to appear on screen

        Args:
            template_path: Path to template image
            timeout: Maximum time to wait (seconds)
            confidence: Confidence threshold (0.0 to 1.0)
            interval: Time between checks (seconds)
            region: Optional region to search

        Returns:
            Result dictionary
        """
        if not self.is_initialized:
            await self.initialize()

        start_time = time.time()
        while time.time() - start_time < timeout:
            result = await self.find_image_on_screen(template_path, confidence, region)
            if result["success"] and result["found"]:
                result["elapsed_time"] = time.time() - start_time
                return result

            await asyncio.sleep(interval)

        return {
            "success": False,
            "error": f"Image not found within {timeout} seconds",
            "timeout": True,
            "elapsed_time": time.time() - start_time
        }

    async def execute_command(
        self,
        command: str,
        timeout: int = 30,
        shell: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a system command

        Args:
            command: Command to execute
            timeout: Timeout in seconds
            shell: Whether to execute in shell

        Returns:
            Result dictionary with output
        """
        if not self.is_initialized:
            await self.initialize()

        # Basic security check - in production would be more robust
        dangerous_commands = ['format', 'del', 'rm', 'shutdown', 'restart', 'mkfs']
        cmd_lower = command.lower().strip()
        for dangerous in dangerous_commands:
            if dangerous in cmd_lower:
                return {
                    "success": False,
                    "error": f"Command contains potentially dangerous operation: {dangerous}"
                }

        try:
            self.logger.info(f"Executing command: {command}")
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=_CREATE_NO_WINDOW,
            ) if shell else await asyncio.create_subprocess_exec(
                *command.split(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=_CREATE_NO_WINDOW,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')

            success = process.returncode == 0

            result = {
                "success": success,
                "command": command,
                "return_code": process.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "pid": process.pid
            }

            if not success:
                result["error"] = f"Command failed with exit code {process.returncode}"
                if stderr_text:
                    result["error"] += f": {stderr_text.strip()}"

            self.logger.info(f"Command executed: {command} (exit code: {process.returncode})")
            return result

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "command": command,
                "timeout": True
            }
        except Exception as e:
            self.logger.error(f"Error executing command {command}: {e}")
            return {
                "success": False,
                "error": f"Failed to execute command: {str(e)}",
                "command": command
            }

    async def get_clipboard(self) -> Dict[str, Any]:
        """
        Get clipboard contents

        Returns:
            Dictionary with clipboard content
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            # Try to get clipboard content
            if self.platform == "windows":
                import win32clipboard
                win32clipboard.OpenClipboard()
                data = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
                content_type = "text"
            elif self.platform == "darwin":  # macOS
                process = await asyncio.create_subprocess_exec(
                    'pbpaste',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await process.communicate()
                data = stdout.decode('utf-8')
                content_type = "text"
            else:  # Linux and others
                try:
                    process = await asyncio.create_subprocess_exec(
                        'xclip', '-selection', 'clipboard', '-o',
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, _ = await process.communicate()
                    data = stdout.decode('utf-8')
                except:
                    # Try alternative
                    process = await asyncio.create_subprocess_exec(
                        'xsel', '--clipboard', '--output',
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, _ = await process.communicate()
                    data = stdout.decode('utf-8')
                content_type = "text"

            self.logger.info("Retrieved clipboard content")
            return {
                "success": True,
                "content": data,
                "type": content_type,
                "length": len(data) if isinstance(data, str) else len(str(data))
            }

        except Exception as e:
            self.logger.error(f"Error getting clipboard: {e}")
            return {
                "success": False,
                "error": f"Failed to get clipboard: {str(e)}"
            }

    async def set_clipboard(self, content: str) -> Dict[str, Any]:
        """
        Set clipboard contents

        Args:
            content: Content to put on clipboard

        Returns:
            Result dictionary
        """
        if not self.is_initialized:
            await self.initialize()

        if not isinstance(content, str):
            content = str(content)

        try:
            if self.platform == "windows":
                import win32clipboard
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_TEXT, content.encode('utf-8'))
                win32clipboard.CloseClipboard()
            elif self.platform == "darwin":  # macOS
                process = await asyncio.create_subprocess_exec(
                    'pbcopy',
                    stdin=asyncio.subprocess.PIPE
                )
                await process.communicate(input=content.encode('utf-8'))
            else:  # Linux and others
                try:
                    process = await asyncio.create_subprocess_exec(
                        'xclip', '-selection', 'clipboard',
                        stdin=asyncio.subprocess.PIPE
                    )
                    await process.communicate(input=content.encode('utf-8'))
                except:
                    # Try alternative
                    process = await asyncio.create_subprocess_exec(
                        'xsel', '--clipboard', '--input',
                        stdin=asyncio.subprocess.PIPE
                    )
                    await process.communicate(input=content.encode('utf-8'))

            self.logger.info(f"Set clipboard content: {len(content)} characters")
            return {
                "success": True,
                "content": content,
                "length": len(content)
            }

        except Exception as e:
            self.logger.error(f"Error setting clipboard: {e}")
            return {
                "success": False,
                "error": f"Failed to set clipboard: {str(e)}"
            }

    async def get_active_window(self) -> Dict[str, Any]:
        """
        Get information about the active window

        Returns:
            Dictionary with window information
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            if self.platform == "windows":
                import win32gui
                import win32process
                hwnd = win32gui.GetForegroundWindow()
                title = win32gui.GetWindowText(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                x, y, x2, y2 = rect
                width = x2 - x
                height = y2 - y

                return {
                    "success": True,
                    "handle": hwnd,
                    "title": title,
                    "pid": pid,
                    "position": (x, y),
                    "size": (width, height),
                    "bounds": {
                        "left": x,
                        "top": y,
                        "right": x2,
                        "bottom": y2
                    }
                }
            elif self.platform == "darwin":  # macOS
                # Using AppleScript
                script = '''
                tell application "System Events"
                    set frontApp to name of first application process whose frontmost is true
                    set frontAppName to name of first application process whose frontmost is true
                end tell
                return frontApp
                '''
                process = await asyncio.create_subprocess_exec(
                    'osascript', '-e', script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await process.communicate()
                title = stdout.decode('utf-8').strip()

                # Get more detailed info would require more complex AppleScript
                return {
                    "success": True,
                    "title": title,
                    "app": title,
                    "note": "Limited info available on macOS without additional permissions"
                }
            else:  # Linux
                try:
                    # Try using xprop and xwininfo
                    # Get active window ID
                    root = await asyncio.create_subprocess_exec(
                        'xprop', '-root', '_NET_ACTIVE_WINDOW',
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, _ = await asyncio.wait_for(root.communicate(), timeout=5.0)
                    output = stdout.decode('utf-8')
                    if '_NET_ACTIVE_WINDOW' in output:
                        window_id = output.split()[-1].strip()
                        # Get window info
                        winfo = await asyncio.create_subprocess_exec(
                            'xwininfo', '-id', window_id,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        wout, _ = await asyncio.wait_for(winfo.communicate(), timeout=5.0)
                        output_text = wout.decode('utf-8')
                        # Parse output (simplified)
                        lines = output_text.split('\n')
                        title = "Unknown"
                        x, y, width, height = 0, 0, 0, 0
                        for line in lines:
                            if 'Title:' in line:
                                title = line.split('Title:', 1)[1].strip()
                            elif 'Absolute upper-left X:' in line:
                                x = int(line.split(':', 1)[1].strip())
                            elif 'Absolute upper-left Y:' in line:
                                y = int(line.split(':', 1)[1].strip())
                            elif 'Width:' in line:
                                width = int(line.split(':', 1)[1].strip())
                            elif 'Height:' in line:
                                height = int(line.split(':', 1)[1].strip())

                        return {
                            "success": True,
                            "title": title,
                            "window_id": window_id,
                            "position": (x, y),
                            "size": (width, height)
                        }
                    else:
                        return {
                            "success": False,
                            "error": "Could not get active window ID"
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to get active window on Linux: {str(e)}"
                    }

        except Exception as e:
            self.logger.error(f"Error getting active window: {e}")
            return {
                "success": False,
                "error": f"Failed to get active window: {str(e)}"
            }

    # ------------------------------------------------------------------
    # Application + window management (Windows-focused)
    # ------------------------------------------------------------------

    def _list_windows_sync(self, limit: int = 40) -> List[Dict[str, Any]]:
        """Enumerate visible top-level windows (handle/title/pid/process)."""
        if self.platform != "windows":
            return []
        import win32gui
        import win32process

        windows = []
        seen = set()

        def _enum(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return
            title = win32gui.GetWindowText(hwnd).strip()
            if not title:
                return
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc_name = ""
                try:
                    proc_name = psutil.Process(pid).name()
                except Exception:
                    pass
            except Exception:
                pid, proc_name = 0, ""
            windows.append({
                "handle": int(hwnd),
                "title": title[:80],
                "pid": pid,
                "process": proc_name,
            })

        try:
            win32gui.EnumWindows(_enum, None)
        except Exception as e:
            self.logger.error(f"Error enumerating windows: {e}")

        # De-duplicate by (process, title)
        dedup = []
        for w in windows:
            key = (w["process"], w["title"])
            if key not in seen:
                seen.add(key)
                dedup.append(w)
        return dedup[:limit]

    async def list_windows(self, limit: int = 40) -> Dict[str, Any]:
        """List open application windows."""
        if not self.is_initialized:
            await self.initialize()
        try:
            windows = await asyncio.to_thread(self._list_windows_sync, limit)
            return {"success": True, "windows": windows, "count": len(windows)}
        except Exception as e:
            self.logger.error(f"Error listing windows: {e}")
            return {"success": False, "error": f"Failed to list windows: {str(e)}"}

    def _find_window_sync(self, query: str) -> Optional[Dict[str, Any]]:
        """Find a visible window by title substring or process name."""
        if self.platform != "windows":
            return None
        import win32gui
        import win32process

        q = query.strip().lower()
        best = None
        title_match = None

        def _enum(hwnd, _):
            nonlocal best, title_match
            if not win32gui.IsWindowVisible(hwnd):
                return
            try:
                title = win32gui.GetWindowText(hwnd).strip()
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc_name = ""
                try:
                    proc_name = psutil.Process(pid).name().lower()
                except Exception:
                    pass
                match = None
                if title and q in title.lower():
                    match = title
                elif proc_name and (q in proc_name or q in proc_name.rsplit(".", 1)[0]):
                    match = title or proc_name
                if match:
                    if best is None or len(match) < len(best):
                        best = match
                        title_match = {
                            "handle": int(hwnd),
                            "title": title,
                            "pid": pid,
                            "process": proc_name,
                        }
            except Exception:
                return

        try:
            win32gui.EnumWindows(_enum, None)
        except Exception as e:
            self.logger.error(f"Error finding window: {e}")
        return title_match

    async def find_window(self, query: str) -> Dict[str, Any]:
        """Find a window by title substring or process name."""
        if not self.is_initialized:
            await self.initialize()
        try:
            window = await asyncio.to_thread(self._find_window_sync, query)
            if not window:
                return {"success": False, "error": f"No window found matching '{query}'"}
            return {"success": True, "window": window}
        except Exception as e:
            return {"success": False, "error": f"Failed to find window: {str(e)}"}

    async def focus_window(self, query: str) -> Dict[str, Any]:
        """Bring a window to the foreground and focus it."""
        if not self.is_initialized:
            await self.initialize()

        def _focus():
            if self.platform != "windows":
                raise RuntimeError("Window focus is only supported on Windows")
            import win32gui
            import win32con
            window = self._find_window_sync(query)
            if not window:
                return None
            hwnd = window["handle"]
            try:
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
                return window
            except Exception as e:
                self.logger.error(f"Error focusing window {hwnd}: {e}")
                return None

        try:
            window = await asyncio.to_thread(_focus)
            if not window:
                return {"success": False, "error": f"No window found matching '{query}'"}
            return {"success": True, "window": window,
                    "message": f"Focused '{window['title'] or window['process']}'"}
        except Exception as e:
            return {"success": False, "error": f"Failed to focus window: {str(e)}"}

    async def move_window(self, query: str, x: int, y: int) -> Dict[str, Any]:
        """Move a window to (x, y). Empty/'*' query targets the active window."""
        if not self.is_initialized:
            await self.initialize()

        def _move():
            import win32gui
            if query in ("", "*"):
                hwnd = win32gui.GetForegroundWindow()
            else:
                window = self._find_window_sync(query)
                if not window:
                    return None
                hwnd = window["handle"]
            _, _, w, h = win32gui.GetWindowRect(hwnd)
            win32gui.MoveWindow(hwnd, x, y, w - x, h - y, True)
            return {"handle": int(hwnd)}

        try:
            window = await asyncio.to_thread(_move)
            if not window:
                return {"success": False, "error": f"No window found matching '{query}'"}
            return {"success": True, "message": f"Moved window to ({x}, {y})"}
        except Exception as e:
            return {"success": False, "error": f"Failed to move window: {str(e)}"}

    async def resize_window(self, query: str, width: int, height: int) -> Dict[str, Any]:
        """Resize a window to (width, height). Empty/'*' query targets the active window."""
        if not self.is_initialized:
            await self.initialize()

        def _resize():
            import win32gui
            if query in ("", "*"):
                hwnd = win32gui.GetForegroundWindow()
            else:
                window = self._find_window_sync(query)
                if not window:
                    return None
                hwnd = window["handle"]
            x, y, _, _ = win32gui.GetWindowRect(hwnd)
            win32gui.MoveWindow(hwnd, x, y, width, height, True)
            return {"handle": int(hwnd)}

        try:
            window = await asyncio.to_thread(_resize)
            if not window:
                return {"success": False, "error": f"No window found matching '{query}'"}
            return {"success": True, "message": f"Resized window to {width}x{height}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to resize window: {str(e)}"}

    async def maximize_window(self, query: str) -> Dict[str, Any]:
        """Maximize a window. Empty/'*' query targets the active window."""
        if not self.is_initialized:
            await self.initialize()

        def _max():
            import win32gui
            import win32con
            if query in ("", "*"):
                hwnd = win32gui.GetForegroundWindow()
            else:
                window = self._find_window_sync(query)
                if not window:
                    return None
                hwnd = window["handle"]
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return {"handle": int(hwnd)}

        try:
            window = await asyncio.to_thread(_max)
            if not window:
                return {"success": False, "error": f"No window found matching '{query}'"}
            return {"success": True, "message": "Window maximized"}
        except Exception as e:
            return {"success": False, "error": f"Failed to maximize window: {str(e)}"}

    async def minimize_window(self, query: str) -> Dict[str, Any]:
        """Minimize a window. Empty/'*' query targets the active window."""
        if not self.is_initialized:
            await self.initialize()

        def _min():
            import win32gui
            import win32con
            if query in ("", "*"):
                hwnd = win32gui.GetForegroundWindow()
            else:
                window = self._find_window_sync(query)
                if not window:
                    return None
                hwnd = window["handle"]
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return {"handle": int(hwnd)}

        try:
            window = await asyncio.to_thread(_min)
            if not window:
                return {"success": False, "error": f"No window found matching '{query}'"}
            return {"success": True, "message": "Window minimized"}
        except Exception as e:
            return {"success": False, "error": f"Failed to minimize window: {str(e)}"}

    async def close_app(self, app_name: str) -> Dict[str, Any]:
        """Gracefully close all windows belonging to an application."""
        if not self.is_initialized:
            await self.initialize()

        def _close():
            if self.platform != "windows":
                raise RuntimeError("App close is only supported on Windows")
            import win32gui
            import win32con
            import win32api
            q = app_name.lower()
            exe = q if q.endswith(".exe") else q + ".exe"
            closed = 0
            found = False

            def _enum(hwnd, _):
                nonlocal closed, found
                if not win32gui.IsWindowVisible(hwnd):
                    return
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    proc_name = ""
                    try:
                        proc_name = psutil.Process(pid).name().lower()
                    except Exception:
                        return
                    if proc_name != exe and q not in proc_name and q not in proc_name.rsplit(".", 1)[0]:
                        return
                    found = True
                    # Request a graceful close
                    win32api.SendMessageTimeout(
                        hwnd, win32con.WM_CLOSE, 0, 0,
                        win32con.SMTO_ABORTIFHUNG, 2000,
                    )
                    closed += 1
                except Exception:
                    return

            try:
                win32gui.EnumWindows(_enum, None)
            except Exception as e:
                self.logger.error(f"Error closing windows: {e}")

            if not found:
                return None
            # Give apps a moment to exit gracefully
            time.sleep(1.0)
            return {"closed": closed, "windows_found": True}

        try:
            result = await asyncio.to_thread(_close)
            if result is None:
                return {"success": False,
                        "error": f"No running application found matching '{app_name}'"}
            return {"success": True, "message": f"Close signal sent to {app_name}",
                    "windows_closed": result["closed"]}
        except Exception as e:
            return {"success": False, "error": f"Failed to close application: {str(e)}"}

    def _resolve_app_path(self, exe: str) -> Optional[str]:
        """Resolve an executable using PATH, common dirs and the App Paths registry."""
        if not exe:
            return None
        found = shutil.which(exe)
        if found:
            return found

        exe_lower = exe.lower()
        common_dirs = [
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
            os.environ.get("LocalAppData", ""),
            os.environ.get("AppData", ""),
        ]
        search_names = [exe_lower, exe_lower.replace(".exe", ""), exe_lower.title()]
        for d in common_dirs:
            if not d:
                continue
            for name in search_names:
                candidate = os.path.join(d, name if name.endswith(".exe") else name + ".exe")
                if os.path.isfile(candidate):
                    return candidate
                # One level of subfolders (apps like "Google\Chrome\Application\chrome.exe")
                try:
                    for entry in os.listdir(d):
                        sub = os.path.join(d, entry, name if name.endswith(".exe") else name + ".exe")
                        if os.path.isfile(sub):
                            return sub
                except Exception:
                    continue

        # App Paths registry lookup
        try:
            import winreg
            for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                key_path = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe_lower}"
                try:
                    with winreg.OpenKey(hive, key_path) as key:
                        value, _ = winreg.QueryValueEx(key, None)
                        if value and os.path.isfile(value):
                            return value
                except OSError:
                    continue
        except Exception:
            pass

        return None

    async def launch_app(self, app_name: str) -> Dict[str, Any]:
        """Launch an application by known name, exe name or URI."""
        if not self.is_initialized:
            await self.initialize()

        try:
            if self.platform != "windows":
                return {"success": False,
                        "error": "Application launching is only supported on Windows"}

            name = app_name.strip().strip('"')
            if not name:
                return {"success": False, "error": "No application name provided"}

            exe = name if name.endswith(".exe") else name + ".exe"

            # URI schemes (ms-settings:, ms-windows-store:, http...)
            if name.startswith("ms-") or "://" in name or name.endswith(".url"):
                os.startfile(name)
                self.logger.info(f"Launched URI: {name}")
                return {"success": True, "message": f"Opened {name}", "target": name}

            # Resolve executable path
            path = await asyncio.to_thread(self._resolve_app_path, exe)
            if path:
                os.startfile(path)
                self.logger.info(f"Launched application: {path}")
                return {"success": True, "message": f"Started {app_name}", "target": path}

            # Last resort: ShellExecute relies on App Paths / shell associations
            import win32api
            try:
                result = win32api.ShellExecute(0, "open", name, None, None, 1)
                if result > 32:
                    self.logger.info(f"Launched via ShellExecute: {name}")
                    return {"success": True, "message": f"Started {app_name}", "target": name}
            except Exception:
                pass

            return {"success": False,
                    "error": f"Could not find or launch '{app_name}'"}
        except Exception as e:
            self.logger.error(f"Error launching app {app_name}: {e}")
            return {"success": False, "error": f"Failed to launch application: {str(e)}"}

    async def list_running_apps(self, limit: int = 20) -> Dict[str, Any]:
        """List running applications (top processes by memory)."""
        if not self.is_initialized:
            await self.initialize()
        try:
            def _apps():
                rows = []
                seen = set()
                for proc in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent"]):
                    try:
                        name = proc.info.get("name") or ""
                        if name in seen:
                            continue
                        seen.add(name)
                        rows.append({
                            "name": name,
                            "pid": proc.info.get("pid"),
                            "memory_percent": round(proc.info.get("memory_percent") or 0, 2),
                            "cpu_percent": round(proc.info.get("cpu_percent") or 0, 2),
                        })
                    except Exception:
                        continue
                rows.sort(key=lambda r: r["memory_percent"], reverse=True)
                return rows[:limit]

            apps = await asyncio.to_thread(_apps)
            return {"success": True, "applications": apps, "count": len(apps)}
        except Exception as e:
            return {"success": False, "error": f"Failed to list applications: {str(e)}"}

    async def wait(self, seconds: float) -> Dict[str, Any]:
        """
        Wait for specified time

        Args:
            seconds: Time to wait (seconds)

        Returns:
            Result dictionary
        """
        if not self.is_initialized:
            await self.initialize()

        if seconds < 0:
            return {
                "success": False,
                "error": "Wait time cannot be negative"
            }

        if seconds > self.max_duration:
            return {
                "success": False,
                "error": f"Wait time exceeds maximum allowed ({self.max_duration} seconds)"
            }

        try:
            await asyncio.sleep(seconds)
            self.logger.info(f"Waited for {seconds} seconds")
            return {
                "success": True,
                "duration": seconds
            }
        except Exception as e:
            self.logger.error(f"Error waiting: {e}")
            return {
                "success": False,
                "error": f"Failed to wait: {str(e)}"
            }

    async def record_macro(
        self,
        actions: List[Dict[str, Any]],
        loop_count: int = 1,
        delay_between_loops: float = 0.0
    ) -> Dict[str, Any]:
        """
        Execute a series of automation actions (macro)

        Args:
            actions: List of action dictionaries
            loop_count: Number of times to repeat the macro
            delay_between_loops: Delay between loop iterations

        Returns:
            Result dictionary
        """
        if not self.is_initialized:
            await self.initialize()

        if not actions:
            return {
                "success": False,
                "error": "No actions provided"
            }

        if loop_count < 1:
            return {
                "success": False,
                "error": "Loop count must be at least 1"
            }

        start_time = time.time()
        total_actions = 0
        successful_actions = 0
        failed_actions = []

        try:
            for loop in range(loop_count):
                if loop > 0 and delay_between_loops > 0:
                    await self.wait(delay_between_loops)

                for action in actions:
                    total_actions += 1
                    action_type = action.get("type", "").lower()

                    try:
                        result = None
                        if action_type == "move":
                            result = await self.move_mouse(
                                action["x"], action["y"],
                                action.get("duration", 0.5)
                            )
                        elif action_type == "click":
                            result = await self.click(
                                action.get("x"), action.get("y"),
                                action.get("button", "left"),
                                action.get("clicks", 1),
                                action.get("interval", 0.0)
                            )
                        elif action_type == "type":
                            result = await self.type_text(
                                action["text"],
                                action.get("interval", 0.01)
                            )
                        elif action_type == "press":
                            result = await self.press_key(action["key"])
                        elif action_type == "hotkey":
                            result = await self.hotkey(*action["keys"])
                        elif action_type == "wait":
                            result = await self.wait(action["seconds"])
                        elif action_type == "scroll":
                            result = await self.scroll(
                                action["clicks"],
                                action.get("x"),
                                action.get("y")
                            )
                        elif action_type == "screenshot":
                            result = await self.take_screenshot(
                                action.get("region")
                            )
                        else:
                            result = {
                                "success": False,
                                "error": f"Unknown action type: {action_type}"
                            }

                        if result and result.get("success"):
                            successful_actions += 1
                        else:
                            failed_actions.append({
                                "action": action,
                                "error": result.get("error", "Unknown error") if result else "No result"
                            })

                    except Exception as e:
                        failed_actions.append({
                            "action": action,
                            "error": str(e)
                        })

            elapsed_time = time.time() - start_time
            self.logger.info(f"Macro executed: {successful_actions}/{total_actions} actions successful in {elapsed_time:.2f}s")

            return {
                "success": len(failed_actions) == 0,
                "total_actions": total_actions,
                "successful_actions": successful_actions,
                "failed_actions": failed_actions,
                "elapsed_time": elapsed_time,
                "loop_count": loop_count
            }

        except Exception as e:
            self.logger.error(f"Error executing macro: {e}")
            return {
                "success": False,
                "error": f"Failed to execute macro: {str(e)}",
                "total_actions": total_actions,
                "successful_actions": successful_actions,
                "failed_actions": failed_actions
            }

    async def shutdown(self):
        """Shutdown the automation tool"""
        self.logger.info("Shutting down Automation Tool")
        self.is_initialized = False