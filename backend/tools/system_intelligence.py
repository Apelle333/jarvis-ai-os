"""
JARVIS AI Operating System - System Intelligence Layer
Provides real awareness of the machine, running modules, hardware, agents,
models and internal state. Every function returns real data.

Security: this layer is READ-ONLY. It never executes commands or mutates
system state.
"""

from __future__ import annotations

import asyncio
import logging
import platform
import subprocess
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import psutil

# Avoid console window flashes when probing tools like nvidia-smi.
_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

if TYPE_CHECKING:
    from core.brain import JARVIS_Brain

logger = logging.getLogger(__name__)

ONLINE = "ONLINE"
OFFLINE = "OFFLINE"
ERROR = "ERROR"
NOT_CONFIGURED = "NOT_CONFIGURED"


def _bytes_human(value: float) -> str:
    """Convert bytes to a human readable string"""
    if value is None:
        return "N/A"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} PB"


class SystemIntelligence:
    """
    System Intelligence Layer - reads real data from the machine and JARVIS
    internals. All methods are read-only and fail gracefully.
    """

    def __init__(self, brain: Optional["JARVIS_Brain"] = None):
        self.brain = brain
        self.logger = logging.getLogger(__name__)
        self.last_scan: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def ollama_host(self) -> str:
        if self.brain is not None:
            return getattr(self.brain.settings, "ollama_host", "http://localhost:11434")
        return "http://localhost:11434"

    def _ollama_client(self):
        try:
            import ollama  # type: ignore

            return ollama
        except Exception:
            return None

    def _get_nvidia_gpus(self) -> Dict[str, Any]:
        """Query NVIDIA GPUs via nvidia-smi (graceful failure)"""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=_CREATE_NO_WINDOW,
            )
            if result.returncode != 0:
                return {"available": False, "gpus": []}

            gpus = []
            for line in result.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 5:
                    continue

                def _num(value: str) -> float:
                    try:
                        return float(value)
                    except (TypeError, ValueError):
                        return 0.0

                gpus.append({
                    "name": parts[0],
                    "utilization_percent": _num(parts[1]),
                    "memory_used_mb": _num(parts[2]),
                    "memory_total_mb": _num(parts[3]),
                    "temperature_c": _num(parts[4]),
                })

            return {"available": True, "gpus": gpus}
        except FileNotFoundError:
            return {"available": False, "gpus": []}
        except Exception as e:
            self.logger.warning(f"nvidia-smi query failed: {e}")
            return {"available": False, "gpus": []}

    # ------------------------------------------------------------------
    # Module discovery
    # ------------------------------------------------------------------

    async def get_active_modules(self) -> Dict[str, Any]:
        """Detect all JARVIS modules and their status"""
        brain = self.brain
        modules: List[Dict[str, Any]] = []

        # --- Backend core ---
        brain_status = OFFLINE
        brain_detail = "not initialized"
        if brain is not None:
            try:
                await brain.get_system_status()
                brain_status = ONLINE
                brain_detail = f"state: {brain.state.value}"
            except Exception as e:
                brain_status = ERROR
                brain_detail = str(e)

        modules.append({
            "name": "Brain",
            "category": "Core",
            "status": brain_status,
            "detail": brain_detail,
        })

        planner_status = ONLINE if (brain is not None and brain.planner is not None) else OFFLINE
        modules.append({
            "name": "Planner",
            "category": "Core",
            "status": planner_status,
            "detail": "task classification and planning" if planner_status == ONLINE else "unavailable",
        })

        router_status = OFFLINE
        if brain is not None and brain.model_router is not None:
            router_status = ONLINE
        modules.append({
            "name": "Model Router",
            "category": "Core",
            "status": router_status,
            "detail": "model selection and routing" if router_status == ONLINE else "unavailable",
        })

        memory_status = OFFLINE
        memory_detail = "not initialized"
        if brain is not None and brain.memory_manager is not None:
            if getattr(brain.memory_manager, "is_initialized", False):
                memory_status = ONLINE
                memory_detail = "SQLite + Vector memory active"
            else:
                memory_status = ERROR
                memory_detail = "memory manager present but not initialized"
        modules.append({
            "name": "Memory Manager",
            "category": "Core",
            "status": memory_status,
            "detail": memory_detail,
        })

        swarm_status = ONLINE if (brain is not None and brain.swarm_manager is not None) else OFFLINE
        modules.append({
            "name": "Swarm Manager",
            "category": "Core",
            "status": swarm_status,
            "detail": (
                f"{len(brain.swarm_manager.agents)} agents registered"
                if swarm_status == ONLINE else "unavailable"
            ),
        })

        # --- AI / Ollama ---
        ollama_status = await self.get_ollama_status()
        if ollama_status.get("server_running"):
            modules.append({
                "name": "Ollama Server",
                "category": "AI",
                "status": ONLINE,
                "detail": f"{len(ollama_status.get('models', []))} models installed",
            })
            loaded = ollama_status.get("loaded_models", [])
            modules.append({
                "name": "Ollama Models",
                "category": "AI",
                "status": ONLINE if loaded else OFFLINE,
                "detail": ", ".join(loaded) if loaded else "no model loaded",
            })
        else:
            modules.append({
                "name": "Ollama Server",
                "category": "AI",
                "status": OFFLINE,
                "detail": "not reachable",
            })
            modules.append({
                "name": "Ollama Models",
                "category": "AI",
                "status": NOT_CONFIGURED,
                "detail": "server unreachable",
            })

        # --- Memory backends ---
        sqlite_ok = False
        if brain is not None and brain.memory_manager is not None:
            sqlite_mem = getattr(brain.memory_manager, "sqlite_memory", None)
            sqlite_ok = sqlite_mem is not None and getattr(sqlite_mem, "is_initialized", False)
        modules.append({
            "name": "SQLite Memory",
            "category": "Memory",
            "status": ONLINE if sqlite_ok else OFFLINE,
            "detail": "short-term conversation store" if sqlite_ok else "unavailable",
        })

        vector_ok = False
        if brain is not None and brain.memory_manager is not None:
            vector_mem = getattr(brain.memory_manager, "vector_memory", None)
            vector_ok = vector_mem is not None and getattr(vector_mem, "is_initialized", False)
        modules.append({
            "name": "Vector Memory",
            "category": "Memory",
            "status": ONLINE if vector_ok else OFFLINE,
            "detail": "ChromaDB long-term store" if vector_ok else "unavailable",
        })

        # --- Agents ---
        agent_statuses = await self.get_agent_status()
        for agent in agent_statuses.get("agents", []):
            modules.append({
                "name": agent.get("name", agent.get("agent_id", "Agent")),
                "category": "Agent",
                "status": ONLINE if agent.get("status") == ONLINE else agent.get("status", OFFLINE),
                "detail": agent.get("agent_type", "specialist"),
            })

        # --- Voice ---
        stt_status = await self._voice_component_status("whisper")
        modules.append({
            "name": "Speech Recognition",
            "category": "Voice",
            "status": stt_status["status"],
            "detail": stt_status["detail"],
        })

        tts_status = await self._voice_component_status("piper")
        modules.append({
            "name": "Text-to-Speech",
            "category": "Voice",
            "status": tts_status["status"],
            "detail": tts_status["detail"],
        })

        online_count = sum(1 for m in modules if m["status"] == ONLINE)
        offline_count = sum(1 for m in modules if m["status"] in (OFFLINE, ERROR, NOT_CONFIGURED))

        return {
            "modules": modules,
            "summary": {
                "total": len(modules),
                "online": online_count,
                "offline": offline_count,
                "timestamp": datetime.now().isoformat(),
            },
        }

    async def _voice_component_status(self, component: str) -> Dict[str, str]:
        """Check STT/TTS availability without importing heavy modules"""
        status = NOT_CONFIGURED
        detail = "not configured"
        try:
            if component == "whisper":
                from voice.whisper import WhisperSTT  # type: ignore

                inst = WhisperSTT()
                info = await inst.get_status()
                if info.get("status") == "ready":
                    status = ONLINE
                    detail = "Whisper ready"
                else:
                    status = NOT_CONFIGURED
                    detail = "Whisper not initialized"
            elif component == "piper":
                from voice.piper import PiperTTS  # type: ignore

                inst = PiperTTS()
                info = await inst.get_status()
                if info.get("status") == "ready":
                    status = ONLINE
                    detail = "Piper ready"
                else:
                    status = NOT_CONFIGURED
                    detail = "Piper not initialized"
        except Exception as e:
            status = ERROR
            detail = str(e)[:80]
        return {"status": status, "detail": detail}

    # ------------------------------------------------------------------
    # Hardware
    # ------------------------------------------------------------------

    async def get_hardware_info(self) -> Dict[str, Any]:
        """Get real hardware information (CPU, GPU, RAM, disk, network)"""
        monitor = self.brain.system_monitor if self.brain else None

        if monitor is not None:
            await monitor._update_metrics()
            with monitor._lock:
                data = monitor.monitor_data.copy()
        else:
            data = {}

        cpu = data.get("cpu", {})
        memory = data.get("memory", {})
        disk = data.get("disk", {})
        network = data.get("network", {})
        processes = data.get("processes", {})

        gpu = self._get_nvidia_gpus()

        ram_total = memory.get("total", 0)
        ram_used = memory.get("used", 0)
        ram_percent = memory.get("percent", 0.0)

        disk_total = disk.get("total", 0)
        disk_free = disk.get("free", 0)
        disk_percent = disk.get("percent", 0.0)

        gpu_summary = None
        if gpu.get("available") and gpu.get("gpus"):
            first = gpu["gpus"][0]
            gpu_summary = {
                "name": first.get("name"),
                "utilization_percent": first.get("utilization_percent", 0.0),
                "memory_used_mb": first.get("memory_used_mb", 0.0),
                "memory_total_mb": first.get("memory_total_mb", 0.0),
                "temperature_c": first.get("temperature_c", 0.0),
            }

        return {
            "success": True,
            "cpu": {
                "usage_percent": cpu.get("usage", 0.0),
                "cores": cpu.get("count", 0),
                "frequency_mhz": cpu.get("freq", 0),
            },
            "gpu": gpu,
            "gpu_summary": gpu_summary,
            "memory": {
                "total": ram_total,
                "used": ram_used,
                "free": max(0, ram_total - ram_used),
                "percent": ram_percent,
                "total_human": _bytes_human(ram_total),
                "used_human": _bytes_human(ram_used),
            },
            "disk": {
                "total": disk_total,
                "used": disk.get("used", 0),
                "free": disk_free,
                "percent": disk_percent,
                "total_human": _bytes_human(disk_total),
                "free_human": _bytes_human(disk_free),
            },
            "network": {
                "bytes_sent": network.get("bytes_sent", 0),
                "bytes_received": network.get("bytes_recv", 0),
            },
            "processes": {
                "total": processes.get("total", 0),
                "running": processes.get("running", 0),
            },
            "host": platform.node(),
            "platform": platform.system(),
            "architecture": platform.machine(),
            "timestamp": datetime.now().isoformat(),
        }

    async def get_running_processes(self, limit: int = 10) -> Dict[str, Any]:
        """Get top running processes by CPU and memory"""
        monitor = self.brain.system_monitor if self.brain else None
        if monitor is not None:
            info = await monitor.get_process_info()
            return {
                "success": info.get("success", False),
                "total": info.get("processes", {}).get("total", 0),
                "running": info.get("processes", {}).get("running", 0),
                "top_by_cpu": info.get("top_by_cpu", [])[:limit],
                "top_by_memory": info.get("top_by_memory", [])[:limit],
                "timestamp": datetime.now().isoformat(),
            }
        return {"success": False, "error": "system monitor unavailable"}

    # ------------------------------------------------------------------
    # Ollama
    # ------------------------------------------------------------------

    async def get_ollama_status(self) -> Dict[str, Any]:
        """Get real Ollama server/model status"""
        client = self._ollama_client()
        if client is None:
            return {
                "server_running": False,
                "server_url": self.ollama_host,
                "models": [],
                "loaded_models": [],
                "error": "ollama python package not installed",
            }

        models: List[Dict[str, Any]] = []
        loaded: List[str] = []
        server_running = False
        error: Optional[str] = None

        try:
            await asyncio.to_thread(client.list)
            server_running = True
        except Exception as e:
            error = f"Ollama server unreachable: {e}"

        if server_running:
            try:
                listing = await asyncio.to_thread(client.list)
                raw_models = getattr(listing, "models", [])
                for m in raw_models:
                    model_name = getattr(m, "model", None)
                    if model_name is None:
                        model_name = m.get("model") if isinstance(m, dict) else None
                    models.append({
                        "name": model_name,
                        "size": getattr(m, "size", 0) if not isinstance(m, dict) else m.get("size", 0),
                        "modified_at": str(getattr(m, "modified_at", "") or ""),
                    })
            except Exception as e:
                error = f"Failed to list models: {e}"

            try:
                ps = await asyncio.to_thread(client.ps)
                raw_loaded = getattr(ps, "models", [])
                for m in raw_loaded:
                    name = getattr(m, "model", None)
                    if name:
                        loaded.append(name)
            except Exception:
                loaded = []

        return {
            "server_running": server_running,
            "server_url": self.ollama_host,
            "models": models,
            "model_names": [m.get("name") for m in models if m.get("name")],
            "loaded_models": loaded,
            "error": error,
        }

    # ------------------------------------------------------------------
    # Agents
    # ------------------------------------------------------------------

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get real status of all registered agents"""
        agents: List[Dict[str, Any]] = []
        swarm = self.brain.swarm_manager if self.brain else None

        if swarm is None or not getattr(swarm, "agents", None):
            return {"agents": agents, "active": 0, "timestamp": datetime.now().isoformat()}

        for agent_type, agent in swarm.agents.items():
            initialized = bool(getattr(agent, "is_initialized", False))
            entry = {
                "agent_id": getattr(agent, "agent_id", str(agent_type)),
                "name": getattr(agent, "agent_name", str(agent_type)),
                "agent_type": getattr(agent, "agent_type", "specialist"),
                "status": ONLINE,
                "initialized": initialized,
                "detail": "registered and initialized" if initialized else "registered, ready on first use",
            }
            try:
                if hasattr(agent, "get_status"):
                    status_info = await agent.get_status()
                    if isinstance(status_info, dict):
                        entry["specializations"] = status_info.get("specializations", [])
            except Exception as e:
                entry["status"] = ERROR
                entry["detail"] = str(e)[:80]
            agents.append(entry)

        active = sum(1 for a in agents if a["status"] == ONLINE)
        return {
            "agents": agents,
            "active": active,
            "timestamp": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------

    async def get_memory_status(self) -> Dict[str, Any]:
        """Get real memory system status"""
        if self.brain is None or self.brain.memory_manager is None:
            return {"is_initialized": False, "short_term": {}, "long_term": {}}

        try:
            stats = await self.brain.memory_manager.get_stats()
        except Exception as e:
            self.logger.error(f"Error getting memory stats: {e}")
            stats = {"error": str(e)}

        return {
            "is_initialized": bool(getattr(self.brain.memory_manager, "is_initialized", False)),
            "short_term": stats.get("short_term", {}),
            "long_term": stats.get("long_term", {}),
            "last_consolidation": stats.get("last_consolidation"),
            "timestamp": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # Application health
    # ------------------------------------------------------------------

    async def get_application_health(self) -> Dict[str, Any]:
        """Get overall application health from real module states"""
        modules = await self.get_active_modules()

        core_statuses = [m["status"] for m in modules["modules"] if m["category"] == "Core"]
        ai_statuses = [m["status"] for m in modules["modules"] if m["category"] == "AI"]

        core_online = all(s == ONLINE for s in core_statuses) if core_statuses else False
        core_any_online = any(s == ONLINE for s in core_statuses)

        if core_online:
            overall = "ONLINE"
        elif core_any_online:
            overall = "DEGRADED"
        else:
            overall = "OFFLINE"

        return {
            "status": overall,
            "core": "ONLINE" if core_online else ("DEGRADED" if core_any_online else "OFFLINE"),
            "ai": "ONLINE" if any(s == ONLINE for s in ai_statuses) else "OFFLINE",
            "online_modules": modules["summary"]["online"],
            "total_modules": modules["summary"]["total"],
            "modules": modules["modules"],
            "timestamp": datetime.now().isoformat(),
        }

    async def get_system_status(self) -> Dict[str, Any]:
        """Get combined status of the whole system"""
        brain = self.brain
        ollama = await self.get_ollama_status()

        status = {
            "application": "ONLINE" if brain is not None else "OFFLINE",
            "brain_state": brain.state.value if brain is not None else "unknown",
            "uptime_seconds": 0,
            "request_count": 0,
            "error_count": 0,
        }

        if brain is not None:
            status["uptime_seconds"] = (datetime.now() - brain.start_time).total_seconds()
            status["request_count"] = brain.request_count
            status["error_count"] = brain.error_count
            status["state"] = brain.state.value

        status["ollama"] = ollama
        status["hardware"] = await self.get_hardware_info()
        status["agents"] = await self.get_agent_status()
        status["memory"] = await self.get_memory_status()
        status["timestamp"] = datetime.now().isoformat()

        return status

    # ------------------------------------------------------------------
    # System scans (memory integration)
    # ------------------------------------------------------------------

    async def store_system_scan(self, summary: str) -> str:
        """Persist a system scan summary into memory"""
        scan_time = datetime.now().isoformat()
        memory_id = None
        if self.brain is not None and self.brain.memory_manager is not None:
            try:
                memory_id = await self.brain.memory_manager.store_knowledge(
                    title="System Scan",
                    content=summary,
                    source="system_intelligence",
                    tags=["system", "scan", "health"],
                    metadata={"scan_time": scan_time},
                )
            except Exception as e:
                self.logger.error(f"Failed to store system scan: {e}")

        self.last_scan = {
            "timestamp": scan_time,
            "summary": summary,
            "memory_id": memory_id,
        }
        return scan_time

    async def get_last_system_scan(self) -> Optional[Dict[str, Any]]:
        """Retrieve the most recent system scan from memory"""
        if self.last_scan is not None:
            return self.last_scan

        if self.brain is None or self.brain.memory_manager is None:
            return None

        try:
            results = await self.brain.memory_manager.search_memory(
                query="system scan health check",
                limit=3,
            )
            for item in results:
                content = item.get("content") or item.get("text") or ""
                if "system" in content.lower() and "scan" in content.lower():
                    return {
                        "timestamp": item.get("timestamp"),
                        "summary": content[:400],
                        "memory_id": item.get("id"),
                    }
        except Exception as e:
            self.logger.error(f"Failed to retrieve last system scan: {e}")

        return None

    # ------------------------------------------------------------------
    # Live snapshot for WebSocket / HUD
    # ------------------------------------------------------------------

    async def get_live_snapshot(self) -> Dict[str, Any]:
        """Lightweight snapshot for real-time HUD updates"""
        monitor = self.brain.system_monitor if self.brain else None
        data = {}
        if monitor is not None:
            with monitor._lock:
                data = monitor.monitor_data.copy()

        brain_state = self.brain.state.value if self.brain is not None else "unknown"
        request_count = self.brain.request_count if self.brain is not None else 0
        error_count = self.brain.error_count if self.brain is not None else 0

        gpu = self._get_nvidia_gpus()
        gpu_summary = None
        if gpu.get("available") and gpu.get("gpus"):
            gpu_summary = gpu["gpus"][0]

        return {
            "brain_state": brain_state,
            "request_count": request_count,
            "error_count": error_count,
            "cpu_percent": data.get("cpu", {}).get("usage", 0.0),
            "memory_percent": data.get("memory", {}).get("percent", 0.0),
            "disk_percent": data.get("disk", {}).get("percent", 0.0),
            "gpu": gpu_summary,
            "gpu_available": gpu.get("available", False),
            "processes_total": data.get("processes", {}).get("total", 0),
            "timestamp": datetime.now().isoformat(),
        }
