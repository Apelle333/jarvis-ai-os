"""
JARVIS AI Operating System - System Monitor Tool
Monitors system resources and health
"""

import asyncio
import logging
import psutil
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


class SystemMonitor:
    """
    System Monitor Tool - Monitors system resources and health
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        self.is_monitoring = False
        self.monitor_thread = None
        self.monitor_data = {
            "cpu": {"usage": 0.0, "count": 0, "freq": 0},
            "memory": {"total": 0, "available": 0, "used": 0, "percent": 0.0},
            "disk": {"total": 0, "used": 0, "free": 0, "percent": 0.0},
            "network": {"bytes_sent": 0, "bytes_recv": 0, "packets_sent": 0, "packets_recv": 0},
            "processes": {"total": 0, "running": 0, "sleeping": 0},
            "boot_time": 0,
            "uptime": 0
        }
        self.history = []  # Store historical data for trends
        self.max_history = 100  # Keep last 100 readings
        self._lock = threading.Lock()

    async def initialize(self):
        """Initialize the system monitor"""
        try:
            self.logger.info("Initializing System Monitor...")
            self.is_initialized = True
            # Get initial readings
            await self._update_metrics()
            self.logger.info("System Monitor initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize System Monitor: {e}")
            raise

    async def start(self):
        """Start monitoring in background"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("System Monitor started")

    async def stop(self):
        """Stop monitoring"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        self.logger.info("System Monitor stopped")

    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.is_monitoring:
            try:
                # Update metrics synchronously for the thread
                self._update_metrics_sync()
                time.sleep(1)  # Update every second
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Wait longer on error

    async def _update_metrics(self):
        """Update system metrics (async version)"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            # Memory
            memory = psutil.virtual_memory()

            # Disk
            disk = psutil.disk_usage('/')

            # Network
            network = psutil.net_io_counters()

            # Processes
            process_count = len(psutil.pids())
            running_count = 0
            sleeping_count = 0
            for proc in psutil.process_iter(['status']):
                try:
                    if proc.info['status'] == 'running':
                        running_count += 1
                    elif proc.info['status'] == 'sleeping':
                        sleeping_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Boot time and uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time

            with self._lock:
                self.monitor_data = {
                    "cpu": {
                        "usage": cpu_percent,
                        "count": cpu_count,
                        "freq": cpu_freq.current if cpu_freq else 0
                    },
                    "memory": {
                        "total": memory.total,
                        "available": memory.available,
                        "used": memory.used,
                        "percent": memory.percent
                    },
                    "disk": {
                        "total": disk.total,
                        "used": disk.used,
                        "free": disk.free,
                        "percent": (disk.used / disk.total) * 100
                    },
                    "network": {
                        "bytes_sent": network.bytes_sent,
                        "bytes_recv": network.bytes_recv,
                        "packets_sent": network.packets_sent,
                        "packets_recv": network.packets_recv
                    },
                    "processes": {
                        "total": process_count,
                        "running": running_count,
                        "sleeping": sleeping_count
                    },
                    "boot_time": boot_time,
                    "uptime": uptime,
                    "timestamp": time.time()
                }

                # Add to history
                self.history.append({
                    "timestamp": time.time(),
                    "cpu_usage": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": (disk.used / disk.total) * 100
                })

                # Keep history size manageable
                if len(self.history) > self.max_history:
                    self.history = self.history[-self.max_history:]

        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")

    def _update_metrics_sync(self):
        """Update system metrics (synchronous version for thread)"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            # Memory
            memory = psutil.virtual_memory()

            # Disk
            disk = psutil.disk_usage('/')

            # Network
            network = psutil.net_io_counters()

            # Processes
            process_count = len(psutil.pids())
            running_count = 0
            sleeping_count = 0
            for proc in psutil.process_iter(['status']):
                try:
                    if proc.info['status'] == 'running':
                        running_count += 1
                    elif proc.info['status'] == 'sleeping':
                        sleeping_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Boot time and uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time

            with self._lock:
                self.monitor_data = {
                    "cpu": {
                        "usage": cpu_percent,
                        "count": cpu_count,
                        "freq": cpu_freq.current if cpu_freq else 0
                    },
                    "memory": {
                        "total": memory.total,
                        "available": memory.available,
                        "used": memory.used,
                        "percent": memory.percent
                    },
                    "disk": {
                        "total": disk.total,
                        "used": disk.used,
                        "free": disk.free,
                        "percent": (disk.used / disk.total) * 100
                    },
                    "network": {
                        "bytes_sent": network.bytes_sent,
                        "bytes_recv": network.bytes_recv,
                        "packets_sent": network.packets_sent,
                        "packets_recv": network.packets_recv
                    },
                    "processes": {
                        "total": process_count,
                        "running": running_count,
                        "sleeping": sleeping_count
                    },
                    "boot_time": boot_time,
                    "uptime": uptime,
                    "timestamp": time.time()
                }

                # Add to history
                self.history.append({
                    "timestamp": time.time(),
                    "cpu_usage": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": (disk.used / disk.total) * 100
                })

                # Keep history size manageable
                if len(self.history) > self.max_history:
                    self.history = self.history[-self.max_history:]

        except Exception as e:
            self.logger.error(f"Error updating metrics (sync): {e}")

    async def get_current_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        try:
            if not self.is_initialized:
                await self.initialize()

            # Trigger an update for fresh data
            await self._update_metrics()

            with self._lock:
                # Return a copy of the data
                return {
                    "success": True,
                    "data": self.monitor_data.copy(),
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            self.logger.error(f"Error getting current stats: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to get system stats: {str(e)}"
            }

    async def get_cpu_info(self) -> Dict[str, Any]:
        """Get detailed CPU information"""
        try:
            if not self.is_initialized:
                await self.initialize()

            await self._update_metrics()

            with self._lock:
                cpu_data = self.monitor_data["cpu"].copy()

            # Get detailed CPU info
            cpu_times = psutil.cpu_times()
            cpu_stats = psutil.cpu_stats()

            result = {
                "success": True,
                "cpu": {
                    "usage_percent": cpu_data["usage"],
                    "core_count": cpu_data["count"],
                    "frequency_mhz": cpu_data["freq"],
                    "times": {
                        "user": cpu_times.user,
                        "system": cpu_times.system,
                        "idle": cpu_times.idle,
                        "nice": getattr(cpu_times, 'nice', 0),
                        "iowait": getattr(cpu_times, 'iowait', 0),
                        "irq": getattr(cpu_times, 'irq', 0),
                        "softirq": getattr(cpu_times, 'softirq', 0),
                        "steal": getattr(cpu_times, 'steal', 0),
                        "guest": getattr(cpu_times, 'guest', 0),
                        "guest_nice": getattr(cpu_times, 'guest_nice', 0)
                    },
                    "stats": {
                        "ctx_switches": cpu_stats.ctx_switches,
                        "interrupts": cpu_stats.interrupts,
                        "soft_interrupts": cpu_stats.soft_interrupts,
                        "syscalls": cpu_stats.syscalls
                    }
                }
            }

            # Per-core usage
            try:
                per_cpu = psutil.cpu_percent(percpu=True)
                result["cpu"]["per_core"] = [{"core": i, "usage": pct} for i, pct in enumerate(per_cpu)]
            except:
                pass

            return result

        except Exception as e:
            self.logger.error(f"Error getting CPU info: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to get CPU info: {str(e)}"
            }

    async def get_memory_info(self) -> Dict[str, Any]:
        """Get detailed memory information"""
        try:
            if not self.is_initialized:
                await self.initialize()

            await self._update_metrics()

            with self._lock:
                mem_data = self.monitor_data["memory"].copy()

            # Get detailed memory info
            swap = psutil.swap_memory()

            result = {
                "success": True,
                "memory": {
                    "total": mem_data["total"],
                    "available": mem_data["available"],
                    "used": mem_data["used"],
                    "percent": mem_data["percent"]
                },
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "free": swap.free,
                    "percent": swap.percent,
                    "sin": swap.sin,
                    "sout": swap.sout
                }
            }

            # Convert to human readable
            def bytes_to_human(bytes_val):
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if bytes_val < 1024.0:
                        return f"{bytes_val:.2f} {unit}"
                    bytes_val /= 1024.0
                return f"{bytes_val:.2f} PB"

            result["memory_human"] = {
                "total": bytes_to_human(mem_data["total"]),
                "available": bytes_to_human(mem_data["available"]),
                "used": bytes_to_human(mem_data["used"]),
                "swap_total": bytes_to_human(swap.total),
                "swap_used": bytes_to_human(swap.used),
                "swap_free": bytes_to_human(swap.free)
            }

            return result

        except Exception as e:
            self.logger.error(f"Error getting memory info: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to get memory info: {str(e)}"
            }

    async def get_disk_info(self) -> Dict[str, Any]:
        """Get disk information"""
        try:
            if not self.is_initialized:
                await self.initialize()

            await self._update_metrics()

            with self._lock:
                disk_data = self.monitor_data["disk"].copy()

            # Get disk partitions
            partitions = []
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partitions.append({
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "opts": part.opts,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": (usage.used / usage.total) * 100
                    })
                except (PermissionError, OSError):
                    # Skip inaccessible drives
                    pass

            # Get disk I/O stats
            try:
                disk_io = psutil.disk_io_counters()
                io_stats = {
                    "read_count": disk_io.read_count,
                    "write_count": disk_io.write_count,
                    "read_bytes": disk_io.read_bytes,
                    "write_bytes": disk_io.write_bytes,
                    "read_time": disk_io.read_time,
                    "write_time": disk_io.write_time
                } if disk_io else {}
            except:
                io_stats = {}

            result = {
                "success": True,
                "disk": {
                    "total": disk_data["total"],
                    "used": disk_data["used"],
                    "free": disk_data["free"],
                    "percent": disk_data["percent"]
                },
                "partitions": partitions,
                "io_stats": io_stats
            }

            # Convert to human readable
            def bytes_to_human(bytes_val):
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if bytes_val < 1024.0:
                        return f"{bytes_val:.2f} {unit}"
                    bytes_val /= 1024.0
                return f"{bytes_val:.2f} PB"

            result["disk_human"] = {
                "total": bytes_to_human(disk_data["total"]),
                "used": bytes_to_human(disk_data["used"]),
                "free": bytes_to_human(disk_data["free"])
            }

            for part in result["partitions"]:
                part["total_human"] = bytes_to_human(part["total"])
                part["used_human"] = bytes_to_human(part["used"])
                part["free_human"] = bytes_to_human(part["free"])

            return result

        except Exception as e:
            self.logger.error(f"Error getting disk info: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to get disk info: {str(e)}"
            }

    async def get_network_info(self) -> Dict[str, Any]:
        """Get network information"""
        try:
            if not self.is_initialized:
                await self.initialize()

            await self._update_metrics()

            with self._lock:
                net_data = self.monitor_data["network"].copy()

            # Get network interfaces
            interfaces = {}
            try:
                for name, addrs in psutil.net_if_addrs().items():
                    addresses = []
                    for addr in addrs:
                        addr_info = {
                            "family": str(addr.family),
                            "address": addr.address,
                            "netmask": addr.netmask,
                            "broadcast": addr.broadcast
                        }
                        addresses.append(addr_info)

                    stats = psutil.net_if_stats().get(name)
                    if stats:
                        interface_stats = {
                            "isup": stats.isup,
                            "duplex": str(stats.duplex),
                            "speed": stats.speed,
                            "mtu": stats.mtu
                        }
                    else:
                        interface_stats = {}

                    interfaces[name] = {
                        "addresses": addresses,
                        "stats": interface_stats
                    }
            except Exception as e:
                self.logger.warning(f"Could not get interface details: {e}")

            # Get network connections (limited)
            connections = []
            try:
                for conn in psutil.net_connections(kind='inet'):
                    if conn.status == 'ESTABLISHED':  # Only established connections
                        connections.append({
                            "fd": conn.fd,
                            "family": str(conn.family),
                            "type": str(conn.type),
                            "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                            "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                            "status": conn.status
                        })
                # Limit to first 20 connections
                connections = connections[:20]
            except Exception as e:
                self.logger.warning(f"Could not get connection details: {e}")

            result = {
                "success": True,
                "network": {
                    "bytes_sent": net_data["bytes_sent"],
                    "bytes_received": net_data["bytes_recv"],
                    "packets_sent": net_data["packets_sent"],
                    "packets_received": net_data["packets_recv"]
                },
                "interfaces": interfaces,
                "connections": connections
            }

            # Convert to human readable
            def bytes_to_human(bytes_val):
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if bytes_val < 1024.0:
                        return f"{bytes_val:.2f} {unit}"
                    bytes_val /= 1024.0
                return f"{bytes_val:.2f} PB"

            result["network_human"] = {
                "sent": bytes_to_human(net_data["bytes_sent"]),
                "received": bytes_to_human(net_data["bytes_recv"]),
                "packets_sent": f"{net_data['packets_sent']:,}",
                "packets_received": f"{net_data['packets_recv']:,}"
            }

            return result

        except Exception as e:
            self.logger.error(f"Error getting network info: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to get network info: {str(e)}"
            }

    async def get_process_info(self) -> Dict[str, Any]:
        """Get process information"""
        try:
            if not self.is_initialized:
                await self.initialize()

            await self._update_metrics()

            with self._lock:
                proc_data = self.monitor_data["processes"].copy()

            # Get top processes by CPU and memory
            processes = []
            try:
                for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'create_time']):
                    try:
                        pinfo = proc.info
                        # Skip system processes we can't access
                        if pinfo['username'] is None:
                            continue

                        processes.append({
                            "pid": pinfo['pid'],
                            "name": pinfo['name'],
                            "username": pinfo['username'],
                            "cpu_percent": pinfo['cpu_percent'] or 0.0,
                            "memory_percent": pinfo['memory_percent'] or 0.0,
                            "create_time": pinfo['create_time']
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
            except Exception as e:
                self.logger.warning(f"Could not get process details: {e}")

            # Sort by CPU usage
            processes_by_cpu = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:10]
            # Sort by memory usage
            processes_by_memory = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:10]

            result = {
                "success": True,
                "processes": {
                    "total": proc_data["total"],
                    "running": proc_data["running"],
                    "sleeping": proc_data["sleeping"]
                },
                "top_by_cpu": processes_by_cpu,
                "top_by_memory": processes_by_memory
            }

            return result

        except Exception as e:
            self.logger.error(f"Error getting process info: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to get process info: {str(e)}"
            }

    async def get_system_uptime(self) -> Dict[str, Any]:
        """Get system uptime information"""
        try:
            if not self.is_initialized:
                await self.initialize()

            await self._update_metrics()

            with self._lock:
                boot_time = self.monitor_data["boot_time"]
                uptime_seconds = self.monitor_data["uptime"]

            # Convert uptime to human readable
            days, remainder = divmod(uptime_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)

            uptime_str = ""
            if days > 0:
                uptime_str += f"{int(days)}d "
            if hours > 0 or days > 0:
                uptime_str += f"{int(hours)}h "
            if minutes > 0 or hours > 0 or days > 0:
                uptime_str += f"{int(minutes)}m "
            uptime_str += f"{int(seconds)}s"

            result = {
                "success": True,
                "boot_time": boot_time,
                "boot_time_datetime": datetime.fromtimestamp(boot_time).isoformat(),
                "uptime_seconds": uptime_seconds,
                "uptime_human": uptime_str.strip()
            }

            return result

        except Exception as e:
            self.logger.error(f"Error getting system uptime: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to get system uptime: {str(e)}"
            }

    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get a performance summary of the system"""
        try:
            if not self.is_initialized:
                await self.initialize()

            await self._update_metrics()

            with self._lock:
                data = self.monitor_data.copy()

            # Calculate performance scores (0-100, higher is better)
            cpu_score = max(0, 100 - data["cpu"]["usage"])
            memory_score = max(0, 100 - data["memory"]["percent"])
            disk_score = max(0, 100 - data["disk"]["percent"])

            overall_score = (cpu_score + memory_score + disk_score) / 3

            # Determine performance level
            if overall_score >= 80:
                performance_level = "Excellent"
            elif overall_score >= 60:
                performance_level = "Good"
            elif overall_score >= 40:
                performance_level = "Fair"
            else:
                performance_level = "Poor"

            result = {
                "success": True,
                "performance": {
                    "overall_score": round(overall_score, 1),
                    "level": performance_level,
                    "cpu_score": round(cpu_score, 1),
                    "memory_score": round(memory_score, 1),
                    "disk_score": round(disk_score, 1)
                },
                "current_usage": {
                    "cpu_percent": data["cpu"]["usage"],
                    "memory_percent": data["memory"]["percent"],
                    "disk_percent": data["disk"]["percent"]
                },
                "timestamp": datetime.now().isoformat()
            }

            return result

        except Exception as e:
            self.logger.error(f"Error getting performance summary: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to get performance summary: {str(e)}"
            }

    async def get_history(self, limit: int = 50) -> Dict[str, Any]:
        """Get historical data for trending"""
        try:
            if not self.is_initialized:
                await self.initialize()

            with self._lock:
                # Return last 'limit' entries
                history_copy = self.history[-limit:] if len(self.history) >= limit else self.history.copy()

            result = {
                "success": True,
                "history": history_copy,
                "count": len(history_copy),
                "max_history": self.max_history
            }

            return result

        except Exception as e:
            self.logger.error(f"Error getting history: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to get history: {str(e)}"
            }

    async def shutdown(self):
        """Shutdown the system monitor"""
        self.logger.info("Shutting down System Monitor")
        await self.stop()
        self.is_initialized = False