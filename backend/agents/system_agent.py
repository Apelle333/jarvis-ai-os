"""
JARVIS AI Operating System - System Agent
Specialized agent for system administration and computer control tasks.

This agent connects the JARVIS Brain to the real Windows machine:
  - Applications: open / close / list running applications
  - Windows: focus / move / resize / maximize / minimize / switch
  - Input: keyboard, mouse, clipboard
  - Files: search / create / organize / list / delete
  - System: CPU / GPU / RAM / disk status, screenshots, diagnostics

Natural language is interpreted by :mod:`core.command_detector`
(bilingual IT/EN). Every action is safety-gated: destructive operations
require explicit user confirmation. Live action events are broadcast over
the WebSocket so the HUD can display the running tool and its result.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
import platform
import psutil
import uuid
import time
import re
import shlex
from collections import deque
from pathlib import Path
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime

from core.personality import Personality
from core.model_router import ModelRouter
from core.planner import TaskType
from core.settings import settings
from core.command_detector import (
    ControlIntent,
    detect_computer_command,
    KNOWN_APPS,
    LOW,
    MEDIUM,
    HIGH,
    CRITICAL,
)
from memory.memory_manager import MemoryManager
from tools.filesystem import FileSystemTool
from tools.terminal import TerminalTool
from tools.system_monitor import SystemMonitor
from tools.automation import AutomationTool
from tools.browser import BrowserTool

if TYPE_CHECKING:
    from core.brain import JARVIS_Brain
    from api.websocket import manager

logger = logging.getLogger(__name__)

# Avoid console window flashes on Windows (windowless backend).
_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

_RISK_ORDER = {LOW: 0, MEDIUM: 1, HIGH: 2, CRITICAL: 3}

_ITALIAN_HINTS = [
    "apri", "chiudi", "cerca", "trova", "crea", "cartella", "finestra", "calcolatrice",
    "stato del pc", "screenshot", "schermata", "cosa c'è", "sposta", "ridimensiona",
    "premi", "digita", "clicca", "organizza", "quali app", "processi", "appunti",
    "esplora", "avvia", "lancia", "fammi", "mi", "il pc", "il computer", "sul desktop",
]


class SystemAgent:
    """
    System Agent - Specialized system administration agent.
    Handles file operations, computer control, application/window management,
    process management, and system monitoring.
    """

    def __init__(self, brain: JARVIS_Brain):
        self.brain = brain
        self.logger = logging.getLogger(__name__)
        self.personality = Personality()
        self.memory_manager = MemoryManager()
        self.model_router = ModelRouter()
        self.filesystem_tool = FileSystemTool()
        self.terminal_tool = TerminalTool()
        self.system_monitor = SystemMonitor()
        self.automation_tool = AutomationTool()
        self.browser_tool = BrowserTool()
        self.system_intelligence = None
        self.is_initialized = False
        self.last_error: Optional[str] = None

        # Computer control state
        self.pending_action: Optional[Dict[str, Any]] = None
        self.action_log: deque = deque(maxlen=settings.action_log_limit)
        self.command_usage: Dict[str, int] = {}
        self._last_lang: str = "en"

        # Agent metadata
        self.agent_id = "system_agent"
        self.agent_name = "System Administrator"
        self.agent_type = "specialist"
        self.specializations = [
            "file_management",
            "system_administration",
            "process_management",
            "application_control",
            "window_management",
            "input_automation",
            "clipboard_operations",
            "screenshots",
            "system_monitoring",
            "performance_optimization",
            "device_management",
            "computer_control",
        ]

        # Supported operations
        self.supported_operations = [
            "create_file", "read_file", "update_file", "delete_file",
            "create_directory", "delete_directory", "copy_file", "move_file",
            "list_directory", "search_files", "organize_files", "get_file_info",
            "run_command", "execute_script", "start_process", "stop_process",
            "list_processes", "get_system_info", "get_network_info",
            "get_disk_usage", "monitor_resources",
            "open_app", "close_app", "list_apps",
            "focus_window", "switch_app", "list_windows",
            "move_window", "resize_window", "maximize_window", "minimize_window",
            "keyboard_type", "keyboard_press", "mouse_click",
            "clipboard_read", "clipboard_set",
            "screenshot", "diagnostics",
        ]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self):
        """Initialize the system agent"""
        try:
            self.logger.info("Initializing System Agent...")
            await self.personality.initialize()
            await self.memory_manager.initialize()
            await self.model_router.initialize()
            await self.filesystem_tool.initialize()
            await self.terminal_tool.initialize()
            await self.system_monitor.start()
            await self.automation_tool.initialize()

            # Reuse the brain's system-intelligence instance when available.
            self.system_intelligence = (
                self.brain.system_intelligence
                if self.brain is not None and getattr(self.brain, "system_intelligence", None)
                else None
            )

            self.is_initialized = True
            self.logger.info("System Agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize System Agent: {e}")
            raise

    async def shutdown(self):
        """Shutdown the agent"""
        self.logger.info("Shutting down System Agent")
        self.is_initialized = False
        await self.filesystem_tool.shutdown()
        await self.terminal_tool.shutdown()
        await self.system_monitor.stop()
        await self.automation_tool.shutdown()

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    async def process_request(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a system-related request.

        Computer-control commands are detected deterministically and executed
        through :meth:`execute_computer_request`; everything else uses the
        classic classify -> model -> execute pipeline.
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            self.logger.info(f"System Agent processing request: {request[:100]}...")

            intent = detect_computer_command(request, pending=self.pending_action)
            if intent is not None:
                return await self.execute_computer_request(request, intent=intent)

            return await self._process_generic(request, context)
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Error in System Agent processing: {e}", exc_info=True)
            error_response = await self.personality.handle_error(str(e))
            return {
                "response": error_response,
                "agent": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                "error": True,
                "metadata": {"agent": self.agent_id, "error": str(e)}
            }

    async def execute_computer_request(
        self,
        text: str,
        intent: Optional[ControlIntent] = None
    ) -> Dict[str, Any]:
        """
        Execute a computer-control command (apps, windows, input, files, system).

        Args:
            text: The original user command (for context/confirmation phrasing).
            intent: A pre-detected :class:`ControlIntent`.

        Returns:
            Dictionary with ``response``, ``data`` and ``metadata``.
        """
        if not self.is_initialized:
            await self.initialize()

        if intent is None:
            intent = detect_computer_command(text, pending=self.pending_action)
        if intent is None:
            return {
                "response": "I did not recognize a computer-control command in that request.",
                "agent": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "metadata": {"action": "unknown", "computer_control": True}
            }

        self._last_lang = "it" if self._is_italian(text) else "en"
        self.command_usage[intent.action] = self.command_usage.get(intent.action, 0) + 1

        # Confirmation handling
        if intent.action == "confirm_pending":
            return await self._handle_confirmation(text, intent.params.get("approved", True))

        # Safety gate
        if self._needs_confirmation(intent):
            return await self._request_confirmation(text, intent)

        self.state = "executing"
        return await self._dispatch(intent, confirmed=True)

    async def confirm_action(self, token: str, approved: bool = True) -> Dict[str, Any]:
        """Confirm or deny a pending action (called from the API / WebSocket)."""
        if not self.pending_action:
            return {
                "success": False,
                "response": "There is no pending action to confirm.",
                "timestamp": datetime.now().isoformat(),
            }
        if self.pending_action.get("token") != token:
            return {
                "success": False,
                "response": "Invalid confirmation token.",
                "timestamp": datetime.now().isoformat(),
            }

        pending = self.pending_action
        intent: ControlIntent = pending["intent"]
        self.pending_action = None

        if not approved:
            self._emit_action(
                phase="cancelled", intent=intent, tool=None,
                message=f"Cancelled {intent.description}"
            )
            self._log_action(intent, "cancelled", "Confirmation declined")
            return {
                "success": True,
                "response": self._phrase_it("Canceled: I will not proceed.", "Annullato: non procedo."),
                "data": {"approved": False},
                "timestamp": datetime.now().isoformat(),
            }

        # Approved -> dispatch with confirmation bypassed
        return await self._dispatch(intent, confirmed=True)

    def has_pending_action(self) -> bool:
        """Whether an action is waiting for user confirmation."""
        return self.pending_action is not None

    def get_pending_action(self) -> Optional[Dict[str, Any]]:
        """Info about the pending action (for the HUD)."""
        if not self.pending_action:
            return None
        intent: ControlIntent = self.pending_action["intent"]
        return {
            "token": self.pending_action.get("token"),
            "action": intent.action,
            "category": intent.category,
            "target": intent.target,
            "description": intent.description,
            "risk": intent.risk,
            "created_at": self.pending_action.get("created_at"),
        }

    def get_action_log(self) -> List[Dict[str, Any]]:
        """Recent executed actions (for the HUD / memory feed)."""
        return list(self.action_log)

    # ------------------------------------------------------------------
    # Confirmation / safety
    # ------------------------------------------------------------------

    def _needs_confirmation(self, intent: ControlIntent) -> bool:
        if not settings.computer_control_enabled:
            return True
        if not settings.enable_confirmation_prompts:
            return False
        threshold = _RISK_ORDER.get(settings.confirmation_threshold, _RISK_ORDER[HIGH])
        return intent.requires_confirmation or _RISK_ORDER.get(intent.risk, 0) >= threshold

    async def _request_confirmation(self, text: str, intent: ControlIntent) -> Dict[str, Any]:
        """Store the action as pending and ask the user to confirm."""
        token = uuid.uuid4().hex[:12]
        self.pending_action = {
            "token": token,
            "intent": intent,
            "created_at": datetime.now().isoformat(),
            "original_text": text,
        }

        phrase = (
            f"Before I proceed, I need your confirmation. I'm about to {intent.description} "
            f"(risk: {intent.risk}). Reply 'yes' to continue or 'no' to cancel."
        )
        if self._is_italian(text):
            phrase = (
                f"Prima di procedere ho bisogno della tua conferma. Sto per {intent.description} "
                f"(rischio: {intent.risk}). Rispondi 'sì' per continuare o 'no' per annullare."
            )

        self._emit_action(
            phase="confirmation_required", intent=intent, tool=None,
            message=phrase, success=True
        )
        self._log_action(intent, "awaiting_confirmation", phrase)

        return {
            "response": phrase,
            "agent": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "needs_confirmation": True,
            "confirmation_token": token,
            "data": {"pending": True, "token": token},
            "metadata": {
                "action": intent.action,
                "category": intent.category,
                "target": intent.target,
                "risk": intent.risk,
                "computer_control": True,
            }
        }

    async def _handle_confirmation(self, text: str, approved: bool) -> Dict[str, Any]:
        """Handle a textual yes/no reply for a pending action."""
        if not self.pending_action:
            return {
                "response": self._phrase_it(
                    "There is no pending action to confirm.",
                    "Non c'è nessuna azione in attesa di conferma."),
                "success": False,
                "timestamp": datetime.now().isoformat(),
            }
        token = self.pending_action.get("token", "")
        return await self.confirm_action(token, approved)

    # ------------------------------------------------------------------
    # Dispatch / execution
    # ------------------------------------------------------------------

    async def _dispatch(self, intent: ControlIntent, confirmed: bool = False) -> Dict[str, Any]:
        """Route an intent to its handler and wrap the result."""
        start = time.time()
        tool = "system_agent"
        try:
            handler = getattr(self, f"_do_{intent.action}", None)
            if handler is None:
                raise ValueError(f"No handler for action '{intent.action}'")

            self._emit_action(
                phase="started", intent=intent, tool=tool,
                message=f"Executing: {intent.description}"
            )
            data = await handler(intent)

            success = bool(data.get("success", False))
            message = data.pop("message", data.get("error", "Action completed"))
            tool = data.get("tool", tool)

            phase = "completed" if success else "failed"
            self._emit_action(phase=phase, intent=intent, tool=tool, message=message,
                              success=success)
            self._log_action(intent, phase, message)

            if success:
                await self._store_action_memory(intent, message, data)

            elapsed = round(time.time() - start, 2)
            return {
                "response": message,
                "agent": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                "success": success,
                "data": data,
                "metadata": {
                    "action": intent.action,
                    "category": intent.category,
                    "target": intent.target,
                    "tool": tool,
                    "risk": intent.risk,
                    "execution_time": elapsed,
                    "confirmed": confirmed,
                    "computer_control": True,
                }
            }
        except Exception as e:
            self.logger.error(f"Error dispatching {intent.action}: {e}", exc_info=True)
            message = f"Failed to {intent.description}: {e}"
            self._emit_action(phase="failed", intent=intent, tool=tool, message=message,
                              success=False)
            self._log_action(intent, "failed", message)
            return {
                "response": message,
                "agent": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "data": {},
                "metadata": {
                    "action": intent.action,
                    "category": intent.category,
                    "target": intent.target,
                    "tool": tool,
                    "risk": intent.risk,
                    "computer_control": True,
                }
            }

    # ------------------------------------------------------------------
    # Handlers: applications
    # ------------------------------------------------------------------

    async def _do_open_app(self, intent: ControlIntent) -> Dict[str, Any]:
        target = intent.target
        launch_target = KNOWN_APPS.get(target, target)
        return await self.automation_tool.launch_app(launch_target)

    async def _do_close_app(self, intent: ControlIntent) -> Dict[str, Any]:
        target = intent.target
        exe = KNOWN_APPS.get(target, target)
        result = await self.automation_tool.close_app(exe)
        if result.get("success"):
            result["message"] = self._phrase_it(
                f"Closed {target}.", f"Ho chiuso {target}.")
        return result

    async def _do_list_apps(self, intent: ControlIntent) -> Dict[str, Any]:
        result = await self.automation_tool.list_running_apps(limit=15)
        if not result.get("success"):
            return result
        apps = result.get("applications", [])
        names = [f"{a['name']} (PID {a['pid']})" for a in apps[:15]]
        result["message"] = self._phrase_it(
            f"Running applications ({len(apps)}): " + ", ".join(names),
            f"Applicazioni in esecuzione ({len(apps)}): " + ", ".join(names),
        )
        return result

    async def _do_list_windows(self, intent: ControlIntent) -> Dict[str, Any]:
        result = await self.automation_tool.list_windows(limit=20)
        if not result.get("success"):
            return result
        wins = result.get("windows", [])
        lines = [f"• {w['title']} [{w['process']}]" for w in wins]
        result["message"] = self._phrase_it(
            f"Open windows ({len(wins)}):\n" + "\n".join(lines),
            f"Finestre aperte ({len(wins)}):\n" + "\n".join(lines),
        )
        return result

    async def _do_focus_window(self, intent: ControlIntent) -> Dict[str, Any]:
        query = intent.target or intent.params.get("raw", "")
        return await self.automation_tool.focus_window(query)

    async def _do_switch_app(self, intent: ControlIntent) -> Dict[str, Any]:
        target = intent.target
        exe = KNOWN_APPS.get(target, target)
        focused = await self.automation_tool.focus_window(target)
        if focused.get("success"):
            return focused
        # Not running -> try to launch it.
        launched = await self.automation_tool.launch_app(exe)
        return launched

    async def _do_move_window(self, intent: ControlIntent) -> Dict[str, Any]:
        x = int(intent.params.get("x", 100))
        y = int(intent.params.get("y", 100))
        query = intent.target or intent.params.get("raw", "")
        return await self.automation_tool.move_window(query or "*", x, y)

    async def _do_resize_window(self, intent: ControlIntent) -> Dict[str, Any]:
        width = int(intent.params.get("width", 800))
        height = int(intent.params.get("height", 600))
        query = intent.target or intent.params.get("raw", "")
        return await self.automation_tool.resize_window(query or "*", width, height)

    async def _do_maximize_window(self, intent: ControlIntent) -> Dict[str, Any]:
        query = intent.target or intent.params.get("raw", "")
        return await self.automation_tool.maximize_window(query or "*")

    async def _do_minimize_window(self, intent: ControlIntent) -> Dict[str, Any]:
        query = intent.target or intent.params.get("raw", "")
        return await self.automation_tool.minimize_window(query or "*")

    # ------------------------------------------------------------------
    # Handlers: input
    # ------------------------------------------------------------------

    async def _do_keyboard_type(self, intent: ControlIntent) -> Dict[str, Any]:
        text = intent.params.get("raw", "") or intent.target
        text = _strip_verb(text, ["digita", "scrivi", "type", "type text", "digita il testo"])
        if not text:
            return {"success": False, "error": "Nothing to type."}
        result = await self.automation_tool.type_text(text)
        if result.get("success"):
            result["message"] = self._phrase_it(
                f"Typed text into the focused window.", "Ho digitato il testo nella finestra attiva.")
        return result

    async def _do_keyboard_press(self, intent: ControlIntent) -> Dict[str, Any]:
        key = intent.params.get("raw", "") or intent.target
        key = _strip_verb(key, ["premi", "press"])
        key_map = {
            "invio": "enter", "enter": "enter", "ent": "enter",
            "tab": "tab", "esc": "escape", "escape": "escape",
            "canc": "delete", "cancella": "delete", "delete": "delete",
            "spazio": "space", "space": "space",
            "win": "win", "windows": "win", "super": "win",
        }
        key = key_map.get(key.strip().lower(), key.strip())
        if not key:
            return {"success": False, "error": "No key specified."}
        return await self.automation_tool.press_key(key)

    async def _do_mouse_click(self, intent: ControlIntent) -> Dict[str, Any]:
        result = await self.automation_tool.click()
        if result.get("success"):
            result["message"] = self._phrase_it("Clicked.", "Ho fatto clic.")
        return result

    async def _do_clipboard_read(self, intent: ControlIntent) -> Dict[str, Any]:
        result = await self.automation_tool.get_clipboard()
        if result.get("success"):
            result["message"] = self._phrase_it(
                f"Clipboard: {result.get('content', '')[:200]}",
                f"Appunti: {result.get('content', '')[:200]}",
            )
        return result

    async def _do_clipboard_set(self, intent: ControlIntent) -> Dict[str, Any]:
        text = intent.params.get("raw", "") or intent.target
        text = _strip_verb(text, ["copia", "copia negli appunti", "copy", "paste", "incolla",
                                  "copy to clipboard"])
        if not text:
            return {"success": False, "error": "Nothing to copy."}
        result = await self.automation_tool.set_clipboard(text)
        if result.get("success"):
            result["message"] = self._phrase_it(
                f"Copied to clipboard: {text[:80]}", f"Copiato negli appunti: {text[:80]}")
        return result

    # ------------------------------------------------------------------
    # Handlers: files
    # ------------------------------------------------------------------

    async def _do_create_folder(self, intent: ControlIntent) -> Dict[str, Any]:
        name = (intent.target or "Nuova cartella").strip(" \"'")
        folder = self._safe_folder_path(name)
        return await self.filesystem_tool.create_directory(folder)

    async def _do_create_file(self, intent: ControlIntent) -> Dict[str, Any]:
        name = (intent.target or "new_file.txt").strip(" \"'")
        return await self.filesystem_tool.create_file(name, intent.params.get("content", ""))

    async def _do_search_files(self, intent: ControlIntent) -> Dict[str, Any]:
        query = (intent.target or intent.params.get("query", "")).strip().strip(" \"'")
        if not query:
            return {"success": False, "error": "What should I search for?"}
        result = await self.filesystem_tool.search_files(pattern=f"*{query}*", directory=".")
        if result.get("success"):
            matches = result.get("matches", [])
            result["message"] = self._phrase_it(
                f"Found {len(matches)} matches for '{query}':\n" + "\n".join(f"• {m}" for m in matches[:12]),
                f"Trovati {len(matches)} risultati per '{query}':\n" + "\n".join(f"• {m}" for m in matches[:12]),
            )
        return result

    async def _do_list_directory(self, intent: ControlIntent) -> Dict[str, Any]:
        directory = intent.params.get("directory", "") or intent.target or "."
        return await self.filesystem_tool.list_directory(directory)

    async def _do_organize_files(self, intent: ControlIntent) -> Dict[str, Any]:
        directory = intent.params.get("directory", "") or ""
        return await self.filesystem_tool.organize_directory(directory)

    async def _do_delete_file(self, intent: ControlIntent) -> Dict[str, Any]:
        name = (intent.target or "").strip().strip(" \"'")
        if not name:
            return {"success": False, "error": "Which file should I delete?"}
        return await self.filesystem_tool.delete_file(name)

    async def _do_delete_folder(self, intent: ControlIntent) -> Dict[str, Any]:
        name = (intent.target or "").strip().strip(" \"'")
        if not name:
            return {"success": False, "error": "Which folder should I delete?"}
        return await self.filesystem_tool.delete_directory(name, recursive=True)

    # ------------------------------------------------------------------
    # Handlers: system
    # ------------------------------------------------------------------

    async def _do_screenshot(self, intent: ControlIntent) -> Dict[str, Any]:
        png = await asyncio.to_thread(self.automation_tool.take_screenshot)
        shot_dir = os.path.join(os.getcwd(), settings.screenshot_dir)
        os.makedirs(shot_dir, exist_ok=True)
        path = os.path.join(shot_dir, f"jarvis_{datetime.now():%Y%m%d_%H%M%S}.png")
        with open(path, "wb") as f:
            f.write(png)
        self.logger.info(f"Screenshot saved: {path}")
        return {
            "success": True,
            "message": self._phrase_it(
                f"Screenshot captured and saved to {path}", f"Schermata catturata e salvata in {path}"),
            "path": path,
            "size": len(png),
        }

    async def _system_data(self) -> Dict[str, Any]:
        if self.system_intelligence is not None:
            return await self.system_intelligence.get_system_status()
        hw = await self.system_monitor.get_performance_summary()
        return {"hardware": hw}

    async def _do_system_status(self, intent: ControlIntent) -> Dict[str, Any]:
        data = await self._system_data()
        hw = data.get("hardware", {}) if isinstance(data, dict) else {}
        cpu = hw.get("cpu", {})
        mem = hw.get("memory", {})
        disk = hw.get("disk", {})
        gpu = hw.get("gpu_summary")

        def human(b):
            try:
                return f"{float(b) / (1024 ** 3):.1f} GB"
            except (TypeError, ValueError):
                return "?"

        lines = [
            f"CPU {cpu.get('usage_percent', '?')}% | {cpu.get('cores', '?')} cores",
            f"RAM {mem.get('percent', '?')}% used",
            f"Disk {disk.get('percent', '?')}% used",
        ]
        if gpu:
            lines.append(f"GPU {gpu.get('name')} @ {gpu.get('utilization_percent', '?')}%")
        else:
            lines.append("GPU: none detected")

        return {
            "success": True,
            "message": self._phrase_it(
                "PC status:\n" + "\n".join(lines),
                "Stato del PC:\n" + "\n".join(lines),
            ),
            "data": data,
        }

    async def _do_cpu_status(self, intent: ControlIntent) -> Dict[str, Any]:
        info = await self.system_monitor.get_cpu_info()
        if not info:
            return {"success": False, "error": "Could not read CPU info."}
        return {
            "success": True,
            "message": self._phrase_it(
                f"CPU usage {info.get('usage_percent', '?')}% over {info.get('total_cores', '?')} cores",
                f"Uso CPU {info.get('usage_percent', '?')}% su {info.get('total_cores', '?')} core"),
            "data": info,
        }

    async def _do_ram_status(self, intent: ControlIntent) -> Dict[str, Any]:
        info = await self.system_monitor.get_memory_info()
        if not info:
            return {"success": False, "error": "Could not read RAM info."}
        def gb(v):
            try:
                return f"{float(v) / (1024 ** 3):.1f} GB"
            except (TypeError, ValueError):
                return "?"
        return {
            "success": True,
            "message": self._phrase_it(
                f"RAM {gb(info.get('used'))} of {gb(info.get('total'))} used ({info.get('percent', '?')}%)",
                f"RAM {gb(info.get('used'))} su {gb(info.get('total'))} in uso ({info.get('percent', '?')}%)"),
            "data": info,
        }

    async def _do_disk_status(self, intent: ControlIntent) -> Dict[str, Any]:
        info = await self.system_monitor.get_disk_info()
        if not info:
            return {"success": False, "error": "Could not read disk info."}
        return {
            "success": True,
            "message": self._phrase_it(
                "Disk usage:\n" + "\n".join(f"• {d.get('device', '?')}: {d.get('percent', '?')}% used" for d in info),
                "Spazio disco:\n" + "\n".join(f"• {d.get('device', '?')}: {d.get('percent', '?')}% in uso" for d in info),
            ),
            "data": info,
        }

    async def _do_gpu_status(self, intent: ControlIntent) -> Dict[str, Any]:
        data = await self._system_data()
        hw = data.get("hardware", {}) if isinstance(data, dict) else {}
        gpu = hw.get("gpu_summary")
        if not gpu:
            return {"success": True, "message": "No discrete GPU detected.", "data": {}}
        return {
            "success": True,
            "message": self._phrase_it(
                f"GPU {gpu.get('name')} @ {gpu.get('utilization_percent', '?')}% | "
                f"{gpu.get('memory_used_mb', '?')}/{gpu.get('memory_total_mb', '?')} MB | "
                f"{gpu.get('temperature_c', '?')} C",
                f"GPU {gpu.get('name')} @ {gpu.get('utilization_percent', '?')}% | "
                f"{gpu.get('memory_used_mb', '?')}/{gpu.get('memory_total_mb', '?')} MB | "
                f"{gpu.get('temperature_c', '?')} C"),
            "data": gpu,
        }

    async def _do_list_processes(self, intent: ControlIntent) -> Dict[str, Any]:
        result = await self.system_intelligence.get_running_processes(limit=10) if self.system_intelligence \
            else await self.system_monitor.get_process_info()
        if not result:
            return {"success": False, "error": "Could not read processes."}
        top = result.get("top_by_cpu", result) if isinstance(result, dict) else result
        if isinstance(top, list):
            lines = [f"• {p.get('name', '?')} CPU {p.get('cpu_percent', 0)}% | MEM {p.get('memory_percent', 0)}%"
                     for p in top[:10]]
            return {"success": True,
                    "message": self._phrase_it("Running processes:\n" + "\n".join(lines),
                                               "Processi in esecuzione:\n" + "\n".join(lines)),
                    "data": result}
        return {"success": True, "message": "Process list unavailable.", "data": result}

    async def _do_diagnostics(self, intent: ControlIntent) -> Dict[str, Any]:
        summary = await self.system_monitor.get_performance_summary()
        uptime = await self.system_monitor.get_system_uptime()
        return {
            "success": True,
            "message": self._phrase_it(
                "Diagnostics:\n" + json_dump(summary),
                "Diagnostica:\n" + json_dump(summary),
            ),
            "data": {"summary": summary, "uptime": uptime},
        }

    async def _do_run_command(self, intent: ControlIntent) -> Dict[str, Any]:
        """Execute a validated or confirmed shell command."""
        command = intent.params.get("command") or intent.target or ""
        if not command:
            return {"success": False, "error": "No command provided."}

        cmd_result = await self.terminal_tool.execute_command(command)
        if cmd_result.get("success"):
            cmd_result["message"] = f"Command executed successfully:\n\n{cmd_result.get('stdout', '')}"
        else:
            cmd_result["message"] = f"Command failed: {cmd_result.get('error', 'Unknown error')}"
        return cmd_result

    # ------------------------------------------------------------------
    # Legacy generic pipeline (non computer-control requests)
    # ------------------------------------------------------------------

    async def _process_generic(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Classic system-agent pipeline: classify -> model -> execute."""
        system_type = await self._classify_system_task(request)
        complexity = await self._assess_complexity(request, context)

        await self.memory_manager.store_conversation(
            role="user",
            content=request,
            modality="text",
            timestamp=datetime.now(),
            metadata={"agent": self.agent_id, "system_type": system_type.value}
        )

        memory_context = await self.memory_manager.get_recent_context(limit=10)
        if context:
            memory_context.append(context)

        model_selection = await self.model_router.select_model(
            task_type=system_type,
            complexity=complexity,
            context=memory_context
        )

        system_result = await self._execute_system_operation(
            request, system_type, context, memory_context
        )

        personalized_response = await self.personality.apply_personality(
            system_result["message"], memory_context, request
        )

        await self.memory_manager.store_conversation(
            role="assistant",
            content=personalized_response,
            modality="text",
            timestamp=datetime.now(),
            metadata={
                "agent": self.agent_id,
                "system_type": system_type.value,
                "complexity": complexity,
                "model_used": model_selection.model_name,
                "operation_success": system_result["success"],
                "operation_type": system_result.get("operation_type", "unknown")
            }
        )

        return {
            "response": personalized_response,
            "agent": self.agent_id,
            "agent_name": self.agent_name,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "system_type": system_type.value,
                "complexity": complexity,
                "model_used": model_selection.model_name,
                "reason": model_selection.reason,
                "operation_success": system_result["success"],
                "operation_type": system_result.get("operation_type", "unknown"),
                "execution_time": system_result.get("execution_time", 0),
                "data": system_result.get("data", {})
            }
        }

    async def _classify_system_task(self, request: str) -> TaskType:
        """Classify the type of system task"""
        request_lower = request.lower()

        if any(word in request_lower for word in ["file", "folder", "directory", "create", "delete", "copy", "move"]):
            return TaskType.FILE_OPERATION
        elif any(word in request_lower for word in ["run", "execute", "command", "terminal", "cmd", "powershell", "bash"]):
            return TaskType.SYSTEM_COMMAND
        elif any(word in request_lower for word in ["process", "service", "task", "program", "application"]):
            return TaskType.SYSTEM_COMMAND
        elif any(word in request_lower for word in ["system", "information", "info", "status", "performance"]):
            return TaskType.SYSTEM_COMMAND
        elif any(word in request_lower for word in ["network", "connection", "internet", "wifi", "ethernet"]):
            return TaskType.SYSTEM_COMMAND
        elif any(word in request_lower for word in ["install", "update", "upgrade", "software", "application"]):
            return TaskType.SYSTEM_COMMAND
        elif any(word in request_lower for word in ["monitor", "watch", "track", "usage", "resource"]):
            return TaskType.SYSTEM_COMMAND
        else:
            return TaskType.SYSTEM_COMMAND

    async def _assess_complexity(self, request: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Assess the complexity of the system task"""
        request_lower = request.lower()

        complex_indicators = ["multiple", "batch", "bulk", "recursive", "scheduled", "automated", "script"]
        simple_indicators = ["single", "one", "simple", "basic", "quick", "show", "list", "check"]

        if any(indicator in request_lower for indicator in complex_indicators):
            return "complex"
        elif any(indicator in request_lower for indicator in simple_indicators):
            return "simple"
        else:
            word_count = len(request.split())
            if word_count > 20:
                return "complex"
            elif word_count > 10:
                return "moderate"
            else:
                return "simple"

    async def _execute_system_operation(
        self,
        request: str,
        system_type: TaskType,
        context: Optional[Dict[str, Any]],
        memory_context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute the system operation based on request type"""
        start_time = datetime.now()

        result = {
            "success": False,
            "message": "",
            "data": {},
            "operation_type": "unknown",
            "execution_time": 0
        }

        try:
            if system_type == TaskType.FILE_OPERATION:
                result = await self._handle_file_operation(request, context)
            elif system_type == TaskType.SYSTEM_COMMAND:
                result = await self._handle_system_command(request, context)
            else:
                result = await self._handle_general_system_request(request, context)

            end_time = datetime.now()
            result["execution_time"] = (end_time - start_time).total_seconds()

        except Exception as e:
            self.logger.error(f"Error executing system operation: {e}")
            result["message"] = f"Operation failed: {str(e)}"
            result["success"] = False

        return result

    async def _handle_file_operation(self, request: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle file and directory operations"""
        request_lower = request.lower()

        params = {}
        if context:
            params.update(context)

        result = {
            "success": False,
            "message": "",
            "data": {},
            "operation_type": "file_operation"
        }

        try:
            if "create" in request_lower and ("file" in request_lower or "document" in request_lower):
                filename = params.get("filename", "new_file.txt")
                content = params.get("content", "# New file created by JARVIS\n")

                file_result = await self.filesystem_tool.create_file(filename, content)
                result.update(file_result)
                result["message"] = f"File '{filename}' created successfully."

            elif "read" in request_lower or "show" in request_lower or "display" in request_lower:
                filename = params.get("filename", "")
                if filename:
                    file_result = await self.filesystem_tool.read_file(filename)
                    result.update(file_result)
                    if file_result["success"]:
                        result["message"] = f"Contents of '{filename}':\n\n{file_result.get('content', '')}"
                    else:
                        result["message"] = f"Failed to read file '{filename}': {file_result.get('error', 'Unknown error')}"
                else:
                    result["message"] = "Please specify a file to read."

            elif "list" in request_lower and ("directory" in request_lower or "folder" in request_lower):
                directory = params.get("directory", ".")
                dir_result = await self.filesystem_tool.list_directory(directory)
                result.update(dir_result)
                if dir_result["success"]:
                    files = dir_result.get("files", [])
                    dirs = dir_result.get("directories", [])
                    result["message"] = f"Contents of '{directory}':\n"
                    if dirs:
                        result["message"] += "Directories:\n" + "\n".join([f"  - {d}" for d in dirs]) + "\n"
                    if files:
                        result["message"] += "Files:\n" + "\n".join([f"  - {f}" for f in files])
                    if not dirs and not files:
                        result["message"] += "  (empty)"
                else:
                    result["message"] = f"Failed to list directory '{directory}': {dir_result.get('error', 'Unknown error')}"

            elif "delete" in request_lower and ("file" in request_lower):
                filename = params.get("filename", "")
                if filename:
                    file_result = await self.filesystem_tool.delete_file(filename)
                    result.update(file_result)
                    if file_result["success"]:
                        result["message"] = f"File '{filename}' deleted successfully."
                    else:
                        result["message"] = f"Failed to delete file '{filename}': {file_result.get('error', 'Unknown error')}"
                else:
                    result["message"] = "Please specify a file to delete."

            else:
                result["message"] = "File operation understood. Please provide more specific details."
                result["success"] = True

        except Exception as e:
            result["message"] = f"Error performing file operation: {str(e)}"
            self.logger.error(f"File operation error: {e}")

        return result

    async def _handle_system_command(self, request: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle system commands and operations"""
        request_lower = request.lower()

        result = {
            "success": False,
            "message": "",
            "data": {},
            "operation_type": "system_command"
        }

        try:
            if "system info" in request_lower or "computer info" in request_lower or "about this pc" in request_lower:
                sys_info = await self._get_system_info()
                result.update({"success": True, "data": sys_info, "message": self._format_system_info(sys_info)})

            elif "cpu" in request_lower and ("usage" in request_lower or "utilization" in request_lower or "performance" in request_lower):
                cpu_info = await self.system_monitor.get_cpu_info()
                result.update({"success": True, "data": cpu_info, "message": self._format_cpu_info(cpu_info)})

            elif "memory" in request_lower or "ram" in request_lower:
                mem_info = await self.system_monitor.get_memory_info()
                result.update({"success": True, "data": mem_info, "message": self._format_memory_info(mem_info)})

            elif "disk" in request_lower or "storage" in request_lower:
                disk_info = await self.system_monitor.get_disk_info()
                result.update({"success": True, "data": disk_info, "message": self._format_disk_info(disk_info)})

            elif "network" in request_lower:
                net_info = await self.system_monitor.get_network_info()
                result.update({"success": True, "data": net_info, "message": self._format_network_info(net_info)})

            elif "process" in request_lower:
                proc_info = await self.system_monitor.get_process_info()
                result.update({"success": True, "data": proc_info, "message": self._format_process_info(proc_info)})

            elif "run" in request_lower or "execute" in request_lower or "esegui" in request_lower or "lancia" in request_lower:
                command = self._extract_command_from_request(request)
                if command:
                    if self._is_command_text_dangerous(request_lower) or self._is_command_text_dangerous(command.lower()):
                        intent = ControlIntent(
                            action="run_command",
                            category="system",
                            target=command,
                            params={"command": command, "original_request": request},
                            risk=HIGH,
                            requires_confirmation=True,
                            description=f"execute the requested command '{command}'"
                        )
                        return await self._request_confirmation(request, intent)

                    base_command = self._get_command_base(command)
                    if base_command and base_command in self.terminal_tool.allowed_commands:
                        cmd_result = await self.terminal_tool.execute_command(command)
                        result.update(cmd_result)
                        self._audit_event("command_executed", command, cmd_result.get("success", False))
                        if cmd_result.get("success"):
                            result["message"] = f"Command executed successfully:\n\n{cmd_result.get('stdout', '')}"
                        else:
                            result["message"] = f"Command failed: {cmd_result.get('error', 'Unknown error')}"
                    else:
                        self.logger.warning(f"[AUDIT] system_command_blocked: {command}")
                        result["message"] = f"Command '{command}' is not allowed for security reasons."
                else:
                    result["message"] = "Please specify what command you'd like to run."

            else:
                sys_info = await self._get_system_info()
                result.update({
                    "success": True,
                    "data": sys_info,
                    "message": f"Here's some basic system information:\n\n{self._format_system_info(sys_info)}\n\nYou can ask for more specific information like CPU usage, memory status, disk space, or network details."
                })

        except Exception as e:
            result["message"] = f"Error executing system command: {str(e)}"
            self.logger.error(f"System command error: {e}")

        return result

    async def _handle_general_system_request(self, request: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle general system requests that don't fit specific categories"""
        result = {
            "success": True,
            "message": f"I understand you want to work with your system regarding: '{request}'. ",
            "data": {},
            "operation_type": "general_system"
        }

        request_lower = request.lower()

        if any(word in request_lower for word in ["help", "what can you do", "cosa puoi fare"]):
            result["message"] += "\n\nI can help you with:\n"
            result["message"] += "• Applications (open, close, list)\n"
            result["message"] += "• Windows (focus, move, resize, switch)\n"
            result["message"] += "• Files (search, create, organize, delete)\n"
            result["message"] += "• System (CPU/GPU/RAM/disk status, screenshots, diagnostics)\n"
            result["message"] += "• Input (keyboard, mouse, clipboard)\n\n"
            result["message"] += "Try things like:\n"
            result["message"] += "- 'JARVIS apri Chrome'\n"
            result["message"] += "- 'JARVIS fai uno screenshot'\n"
            result["message"] += "- 'JARVIS mostrami lo stato del PC'\n"
            result["message"] += "- 'JARVIS crea una cartella chiamata Test'"

        elif any(word in request_lower for word in ["hello", "hi", "hey", "ciao", "salve"]):
            result["message"] += "Hello! I'm your system assistant. How can I help you manage your computer today?"

        else:
            result["message"] += "I can help you with various system administration tasks. Could you please provide more specific details?"

        return result

    # ------------------------------------------------------------------
    # Memory + HUD helpers
    # ------------------------------------------------------------------

    async def _store_action_memory(self, intent: ControlIntent, message: str, data: Dict[str, Any]):
        """Persist successful actions so JARVIS remembers them."""
        try:
            summary = f"{intent.description} -> {message}"
            await self.memory_manager.store_conversation(
                role="assistant",
                content=summary,
                modality="system_action",
                timestamp=datetime.now(),
                metadata={
                    "agent": self.agent_id,
                    "action": intent.action,
                    "category": intent.category,
                    "target": intent.target,
                    "risk": intent.risk,
                    "computer_control": True,
                }
            )
            # Long-term knowledge for important/recurring automations
            if intent.action in ("open_app", "close_app", "switch_app", "create_folder"):
                await self.memory_manager.store_knowledge(
                    title=f"Automation: {intent.action} {intent.target}".strip(),
                    content=summary,
                    source="system_agent",
                    tags=["automation", intent.category, intent.action],
                    metadata={"action": intent.action, "target": intent.target}
                )
        except Exception as e:
            self.logger.warning(f"Failed to store action memory: {e}")

    def _log_action(self, intent: ControlIntent, phase: str, message: str):
        self.action_log.append({
            "action": intent.action,
            "category": intent.category,
            "target": intent.target,
            "risk": intent.risk,
            "phase": phase,
            "message": message[:200],
            "timestamp": datetime.now().isoformat(),
        })

    def _emit_action(self, phase: str, intent: ControlIntent, tool: Optional[str],
                     message: str, success: bool = True):
        """Broadcast an action event to connected HUD clients."""
        try:
            from api.websocket import manager
            asyncio.create_task(manager.broadcast({
                "type": "action",
                "phase": phase,
                "action": intent.action,
                "category": intent.category,
                "target": intent.target,
                "tool": tool,
                "message": message[:300],
                "success": success,
                "risk": intent.risk,
                "timestamp": datetime.now().isoformat(),
            }))
        except Exception as e:
            self.logger.warning(f"Failed to broadcast action event: {e}")

    def _audit_event(self, event: str, detail: str, success: bool = True) -> None:
        """Log audit events for security-sensitive operations."""
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, f"[AUDIT] system_{event}: {detail}")

    def _is_command_text_dangerous(self, text: str) -> bool:
        """Detect potentially destructive natural language in command requests."""
        dangerous_terms = [
            'delete', 'remove', 'erase', 'destroy', 'format', 'shutdown', 'restart', 'reboot',
            'poweroff', 'kill', 'taskkill', 'rmdir', 'rm -rf', 'chmod 777', 'chown', 'net user',
            'net localgroup', 'sc delete', 'sc stop', 'sc config', 'reg add', 'reg delete', 'regedit'
        ]
        return any(term in text for term in dangerous_terms)

    def _get_command_base(self, command: str) -> str:
        """Return the base command token for a shell command."""
        try:
            parts = shlex.split(command, posix=False)
        except ValueError:
            return ""
        return parts[0].lower() if parts else ""

    def _extract_command_from_request(self, request: str) -> str:
        """Extract an explicit command string from a natural language request."""
        text = request.strip()
        if not text:
            return ""

        # Heuristic extraction by removing common wrappers
        prefixes = [
            r"^run\s+", r"^execute\s+", r"^esegui\s+", r"^lancia\s+", r"^avvia\s+",
            r"^esegui il comando\s+", r"^lancia il comando\s+", r"^apri il comando\s+",
            r"^esegui il\s+", r"^lancia il\s+", r"^avvia il\s+"
        ]
        lower_text = text.lower()
        for prefix in prefixes:
            candidate = re.sub(prefix, '', text, flags=re.IGNORECASE).strip()
            if candidate and candidate != text:
                return candidate

        # Extract quoted command if present
        quote_match = re.search(r'"([^"]+)"|\'([^\']+)\'', text)
        if quote_match:
            return quote_match.group(1) or quote_match.group(2)

        # Split on keywords and return the trailing text
        split_keywords = ["run", "execute", "esegui", "lancia", "avvia", "per favore", "please"]
        for keyword in split_keywords:
            if keyword in lower_text:
                parts = re.split(rf"\b{re.escape(keyword)}\b", text, flags=re.IGNORECASE)
                if len(parts) > 1:
                    candidate = parts[-1].strip(' "\'')
                    if candidate:
                        return candidate

        return text

    def _safe_folder_path(self, name: str) -> str:
        """Keep user-created folders inside the sandboxed workspace/current dir."""
        if not name:
            return ""

        normalized = name.strip().strip('"\'')
        candidate = Path(normalized)
        if candidate.is_absolute():
            candidate = Path(*candidate.parts[1:])

        cleaned_parts = [part for part in candidate.parts if part not in ('.', '..', '/', '\\')]
        safe_path = Path(*cleaned_parts)
        return str(safe_path)

    def _is_italian(self, text: str) -> bool:
        lower = text.lower()
        return any(h in lower for h in _ITALIAN_HINTS)

    def _phrase_it(self, en: str, it: str) -> str:
        return it if getattr(self, "_last_lang", "en") == "it" else en

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "is_initialized": self.is_initialized,
            "health_state": "healthy" if self.is_initialized and not self.last_error else ("degraded" if self.last_error else "standby"),
            "last_error": self.last_error,
            "specializations": self.specializations,
            "supported_operations": self.supported_operations,
            "computer_control": {
                "enabled": settings.computer_control_enabled,
                "confirmation_prompt": settings.enable_confirmation_prompts,
                "threshold": settings.confirmation_threshold,
                "pending_action": self.get_pending_action(),
                "recent_actions": list(self.action_log),
                "usage": dict(self.command_usage),
            },
            "last_activity": datetime.now().isoformat()
        }


def _strip_verb(text: str, verbs) -> str:
    """Remove a leading verb/filler from extracted text."""
    t = text
    for v in verbs:
        v = v.lower()
        tl = t.lower()
        if tl.startswith(v):
            t = t[len(v):]
            break
        idx = tl.find(v)
        if idx != -1 and idx < 4:
            t = t[idx + len(v):]
            break
    for f in ["il", "lo", "la", "the", "a", "an", "testo", "text", "nel", "nella"]:
        t = t.strip()
        if t.lower().startswith(f + " "):
            t = t[len(f):]
    return t.strip(" :\"'")


def json_dump(obj: Dict[str, Any]) -> str:
    """Compact JSON dump for diagnostics."""
    import json
    try:
        return json.dumps(obj, indent=2, default=str, ensure_ascii=False)[:2000]
    except Exception:
        return str(obj)
