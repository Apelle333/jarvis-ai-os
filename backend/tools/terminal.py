"""
JARVIS AI Operating System - Terminal Tool
Handles command execution and terminal operations
"""

import asyncio
import logging
import subprocess
import shlex
from pathlib import Path
from typing import Dict, Any, List, Optional
import psutil
import os

from core.settings import settings

logger = logging.getLogger(__name__)

# Avoid console windows when JARVIS (pythonw) spawns shell commands on Windows.
_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class TerminalTool:
    """
    Terminal Tool - Handles command execution and terminal operations
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        self.allowed_commands = {
            # File operations
            'dir', 'ls', 'copy', 'cp', 'move', 'mv', 'del', 'rm', 'ren', 'rename',
            'mkdir', 'rmdir', 'tree',

            # System info
            'systeminfo', 'ver', 'hostname', 'whoami', 'date', 'time',
            'uname', 'uptime', 'w', 'top', 'htop', 'ps', 'tasklist',

            # Network
            'ping', 'ipconfig', 'ifconfig', 'netstat', 'nslookup', 'tracert', 'traceroute',

            # Disk & storage
            'dir', 'ls', 'df', 'du', 'diskpart',

            # Process management
            'taskkill', 'kill', 'pkill', 'pgrep',

            # Development tools
            'git', 'svn', 'hg', 'npm', 'yarn', 'pip', 'pip3', 'python', 'python3',
            'node', 'java', 'javac', 'gcc', 'g++', 'clang', 'make', 'cmake',

            # Utilities
            'echo', 'cat', 'type', 'more', 'less', 'head', 'tail', 'grep', 'find',
            'sort', 'wc', 'cut', 'sed', 'awk', 'curl', 'wget', 'ftp', 'ssh',

            # Compression
            'zip', 'unzip', 'tar', 'gzip', 'gunzip', 'rar', 'unrar',

            # Text editors (read-only)
            'notepad', 'vim', 'nano', 'emacs'
        }

        self.blocked_commands = {
            # Dangerous system commands
            'format', 'fdisk', 'diskpart', 'reg', 'regedit',
            'shutdown', 'restart', 'logoff', 'logout', 'exit',
            'del *', 'rm -rf', 'format', 'chkdsk', 'defrag',

            # Security risks
            'net user', 'net localgroup', 'net stop', 'net start',
            'sc ', 'services.msc', 'taskmgr', 'msconfig',
            'reg add', 'reg delete', 'reg modify',

            # Network attacks
            'netsh', 'iptables', 'ufw', 'firewall-cmd',

            # Privilege escalation
            'runas', 'sudo', 'su', 'psexec',

            # Dangerous PowerShell
            'Invoke-Expression', 'IEX', 'Start-Process',

            # File system destruction
            '>', '>>', '|', '&', '&&', '||',  # These need special handling
        }

    async def initialize(self):
        """Initialize the terminal tool"""
        try:
            self.logger.info("Initializing Terminal Tool...")
            self.is_initialized = True
            self.logger.info("Terminal Tool initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Terminal Tool: {e}")
            raise

    def _is_command_allowed(self, command: str) -> bool:
        """Check if a command is allowed to run"""
        if not command or not command.strip():
            return False

        cmd_lower = command.strip().lower()

        # Check for blocked patterns
        for blocked in self.blocked_commands:
            if blocked in cmd_lower:
                return False

        if any(op in cmd_lower for op in ['&&', '||', ';', '|', '>', '<', '$(', '`']):
            return False

        # Extract the base command (first word)
        try:
            parts = shlex.split(command, posix=False)
        except ValueError:
            return False

        if not parts:
            return False

        base_command = parts[0].lower()
        return base_command in self.allowed_commands

    def _sanitize_command(self, command: str) -> str:
        """Sanitize command input"""
        if not command:
            return ""

        # Remove dangerous shell operators and characters
        dangerous = ['&', '|', ';', '$', '`', '>', '<', '(', ')', '{', '}']
        for char in dangerous:
            command = command.replace(char, '')

        # Collapse repeated whitespace
        command = ' '.join(command.split())

        # Limit length
        if len(command) > 500:
            command = command[:500]

        return command.strip()

    def _is_path_safe(self, path: str) -> bool:
        """Ensure the working directory remains inside the configured workspace root."""
        if not path:
            return False
        try:
            target_path = Path(path).resolve()
            base_path = Path(settings.workspace_root).resolve()
            try:
                target_path.relative_to(base_path)
                return True
            except ValueError:
                return False
        except Exception:
            return False

    def _audit_event(self, event: str, detail: str, success: bool = True, extra: str = "") -> None:
        """Log security-related and audit-relevant terminal events."""
        message = f"[AUDIT] {event}: {detail}"
        if extra:
            message += f" | {extra}"
        if success:
            self.logger.info(message)
        else:
            self.logger.warning(message)

    async def execute_command(
        self,
        command: str,
        timeout: int = 30,
        cwd: Optional[str] = None,
        capture_output: bool = True
    ) -> Dict[str, Any]:
        """Execute a command and return the result"""
        try:
            if not self.is_initialized:
                await self.initialize()

            # Security check
            if not self._is_command_allowed(command):
                self._audit_event("command_blocked", command, False, "Disallowed command or blocked pattern")
                return {
                    "success": False,
                    "error": f"Command '{command}' is not allowed for security reasons",
                    "command": command
                }

            # Sanitize input
            sanitized_command = self._sanitize_command(command)
            if not sanitized_command:
                self._audit_event("command_blocked", command, False, "Invalid command after sanitization")
                return {
                    "success": False,
                    "error": "Invalid command after sanitization",
                    "command": command
                }

            self._audit_event("command_allowed", sanitized_command, True)

            # Set working directory to the configured workspace root by default.
            if cwd is None:
                cwd = str(Path(settings.workspace_root).resolve())
            else:
                # Ensure cwd is safe
                if not self._is_path_safe(cwd):
                    self._audit_event("command_blocked", command, False, f"Unsafe working directory: {cwd}")
                    return {
                        "success": False,
                        "error": f"Working directory '{cwd}' is not allowed for security reasons",
                        "command": sanitized_command
                    }

            # Execute command
            process = await asyncio.create_subprocess_shell(
                sanitized_command,
                stdout=asyncio.subprocess.PIPE if capture_output else None,
                stderr=asyncio.subprocess.PIPE if capture_output else None,
                cwd=cwd,
                creationflags=_CREATE_NO_WINDOW,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds",
                    "command": sanitized_command,
                    "timeout": True
                }

            # Decode output
            stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""

            success = process.returncode == 0

            result = {
                "success": success,
                "command": sanitized_command,
                "return_code": process.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "pid": process.pid
            }

            if not success:
                result["error"] = f"Command failed with exit code {process.returncode}"
                if stderr_text:
                    result["error"] += f": {stderr_text.strip()}"

            self.logger.info(f"Command executed: {sanitized_command} (exit code: {process.returncode})")
            return result

        except Exception as e:
            self.logger.error(f"Error executing command {command}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to execute command: {str(e)}",
                "command": command
            }

    async def execute_script(
        self,
        script_content: str,
        script_type: str = "batch",  # batch, powershell, bash, sh, python
        timeout: int = 60
    ) -> Dict[str, Any]:
        """Execute a script"""
        try:
            if not self.is_initialized:
                await self.initialize()

            # Security check for scripts
            dangerous_patterns = [
                'format', 'del', 'rm', 'destroy', 'delete', 'remove',
                'shutdown', 'restart', 'reboot', 'halt', 'poweroff',
                'net user', 'net localgroup', 'add user', 'del user',
                'reg add', 'reg delete', 'sc create', 'sc delete'
            ]

            script_lower = script_content.lower()
            for pattern in dangerous_patterns:
                if pattern in script_lower:
                    self._audit_event("script_blocked", pattern, False, f"Dangerous pattern detected in script")
                    return {
                        "success": False,
                        "error": f"Script contains potentially dangerous content: '{pattern}'",
                        "script_type": script_type
                    }

            if any(op in script_lower for op in ['&&', '||', ';', '|', '>', '<', '$(', '`']):
                self._audit_event("script_blocked", script_content, False, "Unsafe shell operators detected")
                return {
                    "success": False,
                    "error": "Script contains unsafe shell operators",
                    "script_type": script_type
                }

            # Determine interpreter based on script type
            if script_type.lower() in ['batch', 'bat']:
                cmd = ['cmd', '/c']
                ext = '.bat'
            elif script_type.lower() in ['powershell', 'ps1']:
                cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File']
                ext = '.ps1'
            elif script_type.lower() in ['bash', 'sh']:
                cmd = ['bash']
                ext = '.sh'
            elif script_type.lower() == 'python':
                cmd = ['python']
                ext = '.py'
            else:
                return {
                    "success": False,
                    "error": f"Unsupported script type: {script_type}",
                    "script_type": script_type
                }

            # Create temporary script file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix=ext, delete=False) as f:
                f.write(script_content)
                script_path = f.name

            try:
                # Add script path to command
                cmd.append(script_path)

                # Execute the script
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    creationflags=_CREATE_NO_WINDOW,
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                # Decode output
                stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
                stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""

                success = process.returncode == 0

                result = {
                    "success": success,
                    "script_type": script_type,
                    "script_path": script_path,
                    "return_code": process.returncode,
                    "stdout": stdout_text,
                    "stderr": stderr_text
                }

                if not success:
                    result["error"] = f"Script failed with exit code {process.returncode}"
                    if stderr_text:
                        result["error"] += f": {stderr_text.strip()}"

                self.logger.info(f"Script executed: {script_type} (exit code: {process.returncode})")
                return result

            finally:
                # Clean up temporary file
                try:
                    os.unlink(script_path)
                except:
                    pass

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Script execution timed out after {timeout} seconds",
                "script_type": script_type,
                "timeout": True
            }
        except Exception as e:
            self.logger.error(f"Error executing script: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to execute script: {str(e)}",
                "script_type": script_type
            }

    async def get_running_processes(self) -> Dict[str, Any]:
        """Get list of running processes"""
        try:
            if not self.is_initialized:
                await self.initialize()

            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    # Only include processes we have permission to see
                    if pinfo['username'] is not None:
                        processes.append({
                            'pid': pinfo['pid'],
                            'name': pinfo['name'],
                            'username': pinfo['username'],
                            'cpu_percent': pinfo['cpu_percent'] or 0.0,
                            'memory_percent': pinfo['memory_percent'] or 0.0
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)

            self.logger.info(f"Retrieved {len(processes)} running processes")
            return {
                "success": True,
                "processes": processes[:50],  # Limit to top 50
                "count": len(processes)
            }

        except Exception as e:
            self.logger.error(f"Error getting running processes: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to get running processes: {str(e)}"
            }

    async def kill_process(self, pid: int) -> Dict[str, Any]:
        """Kill a process by PID"""
        try:
            if not self.is_initialized:
                await self.initialize()

            try:
                proc = psutil.Process(pid)
                proc_name = proc.name()
                proc.terminate()

                # Wait for process to terminate
                try:
                    proc.wait(timeout=5)
                except psutil.TimeoutExpired:
                    proc.kill()  # Force kill if terminate doesn't work
                    proc.wait(timeout=5)

                self.logger.info(f"Process killed: PID {pid} ({proc_name})")
                return {
                    "success": True,
                    "message": f"Process {pid} ({proc_name}) terminated successfully",
                    "pid": pid
                }
            except psutil.NoSuchProcess:
                return {
                    "success": False,
                    "error": f"No process found with PID {pid}"
                }
            except psutil.AccessDenied:
                return {
                    "success": False,
                    "error": f"Access denied to terminate process {pid}"
                }

        except Exception as e:
            self.logger.error(f"Error killing process {pid}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to kill process: {str(e)}"
            }

    async def get_environment_variables(self) -> Dict[str, Any]:
        """Get environment variables"""
        try:
            if not self.is_initialized:
                await self.initialize()

            env_vars = dict(os.environ)

            # Filter out potentially sensitive variables
            sensitive_keys = ['PASSWORD', 'SECRET', 'KEY', 'TOKEN', 'AUTH', 'CREDENTIAL']
            filtered_env = {}
            for key, value in env_vars.items():
                if any(sensitive in key.upper() for sensitive in sensitive_keys):
                    filtered_env[key] = "[REDACTED]"
                else:
                    filtered_env[key] = value

            self.logger.info(f"Retrieved {len(env_vars)} environment variables")
            return {
                "success": True,
                "environment_variables": filtered_env,
                "count": len(env_vars)
            }

        except Exception as e:
            self.logger.error(f"Error getting environment variables: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to get environment variables: {str(e)}"
            }

    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            if not self.is_initialized:
                await self.initialize()

            # Get basic system info
            uname = os.uname() if hasattr(os, 'uname') else None

            info = {
                "platform": os.name,
                "system": platform.system() if 'platform' in globals() else "Unknown",
                "release": platform.release() if 'platform' in globals() else "Unknown",
                "version": platform.version() if 'platform' in globals() else "Unknown",
                "machine": platform.machine() if 'platform' in globals() else "Unknown",
                "processor": platform.processor() if 'platform' in globals() else "Unknown",
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "boot_time": psutil.boot_time()
            }

            # Add platform-specific info
            if hasattr(os, 'uname'):
                uname_info = os.uname()
                info.update({
                    "sysname": uname_info.sysname,
                    "nodename": uname_info.nodename,
                    "release": uname_info.release,
                    "version": uname_info.version,
                    "machine": uname_info.machine
                })

            self.logger.info("Retrieved system information")
            return {
                "success": True,
                "system_info": info
            }

        except Exception as e:
            self.logger.error(f"Error getting system info: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to get system information: {str(e)}"
            }

    async def shutdown(self):
        """Shutdown the terminal tool"""
        self.logger.info("Shutting down Terminal Tool")
        self.is_initialized = False


# Import platform at module level to avoid issues
import platform