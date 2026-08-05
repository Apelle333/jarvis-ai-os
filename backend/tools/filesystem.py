"""
JARVIS AI Operating System - File System Tool
Handles file and directory operations
"""

import asyncio
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import aiofiles

from core.settings import settings

logger = logging.getLogger(__name__)


class FileSystemTool:
    """
    File System Tool - Handles file and directory operations
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        self.base_path = Path(settings.workspace_root).resolve()
        self.allowed_extensions = {
            '.txt', '.md', '.json', '.xml', '.html', '.css', '.js', '.ts',
            '.py', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs', '.php',
            '.rb', '.swift', '.kt', '.scala', '.r', '.m', '.mm', '.pl', '.pm',
            '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
            '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
            '.sql', '.db', '.sqlite', '.csv', '.tsv',
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp',
            '.mp3', '.wav', '.ogg', '.flac', '.aac',
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
            '.js', '.json', '.jsx', '.tsx', '.vue', '.svelte'
        }
        self.blocked_paths = {
            '/', '\\', 'C:\\', 'D:\\', 'E:\\',  # Root drives
            '/System', '/Library', '/Users',  # macOS system dirs
            '/proc', '/sys', '/dev', '/boot',  # Linux system dirs
            'Windows', 'Program Files', 'Program Files (x86)',  # Windows system dirs
        }

    async def initialize(self):
        """Initialize the file system tool"""
        try:
            self.logger.info("Initializing File System Tool...")
            # Ensure base directory exists
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.is_initialized = True
            self.logger.info("File System Tool initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize File System Tool: {e}")
            raise

    def _audit_event(self, event: str, detail: str, success: bool = True) -> None:
        """Log security-related filesystem events."""
        level = logging.INFO if success else logging.WARNING
        logger.log(level, f"[AUDIT] filesystem_{event}: {detail}")

    def _is_path_safe(self, path: str) -> bool:
        """Check if a path is safe to access"""
        try:
            # Resolve relative paths against the configured workspace root.
            target_path = (self.base_path / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()

            # Check if path is within base directory
            try:
                target_path.relative_to(self.base_path)
            except ValueError:
                self._audit_event("blocked_path", f"Path outside workspace: {path}", False)
                return False

            # Check against blocked paths
            path_str = str(target_path).lower()
            for blocked in self.blocked_paths:
                if blocked.lower() in path_str:
                    self._audit_event("blocked_path", f"Blocked path pattern matched: {path}", False)
                    return False

            return True
        except Exception:
            self._audit_event("blocked_path", f"Path validation failed: {path}", False)
            return False

    def _is_extension_allowed(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        if not filename:
            return False
        extension = Path(filename).suffix.lower()
        return extension in self.allowed_extensions

    async def create_file(self, filename: str, content: str = "") -> Dict[str, Any]:
        """Create a new file"""
        try:
            if not self.is_initialized:
                await self.initialize()

            if not self._is_path_safe(filename):
                return {
                    "success": False,
                    "error": f"Access to path '{filename}' is not allowed for security reasons"
                }

            if not self._is_extension_allowed(filename):
                return {
                    "success": False,
                    "error": f"File type not allowed for '{filename}'"
                }

            # Ensure directory exists
            file_path = self.base_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)

            self.logger.info(f"File created: {filename}")
            return {
                "success": True,
                "message": f"File '{filename}' created successfully",
                "file_path": str(file_path),
                "size": len(content)
            }

        except Exception as e:
            self.logger.error(f"Error creating file {filename}: {e}")
            return {
                "success": False,
                "error": f"Failed to create file: {str(e)}"
            }

    async def read_file(self, filename: str) -> Dict[str, Any]:
        """Read a file"""
        try:
            if not self.is_initialized:
                await self.initialize()

            if not self._is_path_safe(filename):
                return {
                    "success": False,
                    "error": f"Access to path '{filename}' is not allowed for security reasons"
                }

            file_path = self.base_path / filename
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File '{filename}' not found"
                }

            if not file_path.is_file():
                return {
                    "success": False,
                    "error": f"'{filename}' is not a file"
                }

            # Read file
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()

            self.logger.info(f"File read: {filename}")
            return {
                "success": True,
                "content": content,
                "file_path": str(file_path),
                "size": len(content)
            }

        except Exception as e:
            self.logger.error(f"Error reading file {filename}: {e}")
            return {
                "success": False,
                "error": f"Failed to read file: {str(e)}"
            }

    async def update_file(self, filename: str, content: str, append: bool = False) -> Dict[str, Any]:
        """Update an existing file"""
        try:
            if not self.is_initialized:
                await self.initialize()

            if not self._is_path_safe(filename):
                return {
                    "success": False,
                    "error": f"Access to path '{filename}' is not allowed for security reasons"
                }

            file_path = self.base_path / filename
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File '{filename}' not found"
                }

            # Write file (append or overwrite)
            mode = 'a' if append else 'w'
            async with aiofiles.open(file_path, mode, encoding='utf-8') as f:
                await f.write(content)

            self.logger.info(f"File updated: {filename} ({'appended' if append else 'overwritten'})")
            return {
                "success": True,
                "message": f"File '{filename}' {'appended to' if append else 'updated'} successfully",
                "file_path": str(file_path),
                "size": len(content)
            }

        except Exception as e:
            self.logger.error(f"Error updating file {filename}: {e}")
            return {
                "success": False,
                "error": f"Failed to update file: {str(e)}"
            }

    async def delete_file(self, filename: str) -> Dict[str, Any]:
        """Delete a file"""
        try:
            if not self.is_initialized:
                await self.initialize()

            if not self._is_path_safe(filename):
                return {
                    "success": False,
                    "error": f"Access to path '{filename}' is not allowed for security reasons"
                }

            file_path = self.base_path / filename
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File '{filename}' not found"
                }

            if not file_path.is_file():
                return {
                    "success": False,
                    "error": f"'{filename}' is not a file"
                }

            # Delete file
            file_path.unlink()

            self.logger.info(f"File deleted: {filename}")
            return {
                "success": True,
                "message": f"File '{filename}' deleted successfully"
            }

        except Exception as e:
            self.logger.error(f"Error deleting file {filename}: {e}")
            return {
                "success": False,
                "error": f"Failed to delete file: {str(e)}"
            }

    async def create_directory(self, directory: str) -> Dict[str, Any]:
        """Create a new directory"""
        try:
            if not self.is_initialized:
                await self.initialize()

            if not self._is_path_safe(directory):
                return {
                    "success": False,
                    "error": f"Access to path '{directory}' is not allowed for security reasons"
                }

            dir_path = self.base_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)

            self.logger.info(f"Directory created: {directory}")
            return {
                "success": True,
                "message": f"Directory '{directory}' created successfully",
                "directory_path": str(dir_path)
            }

        except Exception as e:
            self.logger.error(f"Error creating directory {directory}: {e}")
            return {
                "success": False,
                "error": f"Failed to create directory: {str(e)}"
            }

    async def delete_directory(self, directory: str, recursive: bool = False) -> Dict[str, Any]:
        """Delete a directory"""
        try:
            if not self.is_initialized:
                await self.initialize()

            if not self._is_path_safe(directory):
                return {
                    "success": False,
                    "error": f"Access to path '{directory}' is not allowed for security reasons"
                }

            dir_path = self.base_path / directory
            if not dir_path.exists():
                return {
                    "success": False,
                    "error": f"Directory '{directory}' not found"
                }

            if not dir_path.is_dir():
                return {
                    "success": False,
                    "error": f"'{directory}' is not a directory"
                }

            # Delete directory
            if recursive:
                shutil.rmtree(dir_path)
            else:
                dir_path.rmdir()  # Only works if directory is empty

            self.logger.info(f"Directory deleted: {directory} ({'recursive' if recursive else 'empty'})")
            return {
                "success": True,
                "message": f"Directory '{directory}' deleted successfully"
            }

        except Exception as e:
            self.logger.error(f"Error deleting directory {directory}: {e}")
            return {
                "success": False,
                "error": f"Failed to delete directory: {str(e)}"
            }

    async def list_directory(self, directory: str = ".") -> Dict[str, Any]:
        """List contents of a directory"""
        try:
            if not self.is_initialized:
                await self.initialize()

            if not self._is_path_safe(directory):
                return {
                    "success": False,
                    "error": f"Access to path '{directory}' is not allowed for security reasons"
                }

            dir_path = self.base_path / directory
            if not dir_path.exists():
                return {
                    "success": False,
                    "error": f"Directory '{directory}' not found"
                }

            if not dir_path.is_dir():
                return {
                    "success": False,
                    "error": f"'{directory}' is not a directory"
                }

            # List directory contents
            files = []
            directories = []

            for item in dir_path.iterdir():
                if item.is_file():
                    files.append(item.name)
                elif item.is_dir():
                    directories.append(item.name)

            self.logger.info(f"Directory listed: {directory}")
            return {
                "success": True,
                "directory": str(dir_path),
                "files": sorted(files),
                "directories": sorted(directories),
                "file_count": len(files),
                "directory_count": len(directories)
            }

        except Exception as e:
            self.logger.error(f"Error listing directory {directory}: {e}")
            return {
                "success": False,
                "error": f"Failed to list directory: {str(e)}"
            }

    async def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy a file"""
        try:
            if not self.is_initialized:
                await self.initialize()

            if not self._is_path_safe(source) or not self._is_path_safe(destination):
                return {
                    "success": False,
                    "error": "Access to one or both paths is not allowed for security reasons"
                }

            source_path = self.base_path / source
            dest_path = self.base_path / destination

            if not source_path.exists():
                return {
                    "success": False,
                    "error": f"Source file '{source}' not found"
                }

            if not source_path.is_file():
                return {
                    "success": False,
                    "error": f"'{source}' is not a file"
                }

            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(source_path, dest_path)

            self.logger.info(f"File copied: {source} -> {destination}")
            return {
                "success": True,
                "message": f"File '{source}' copied to '{destination}' successfully",
                "source_path": str(source_path),
                "destination_path": str(dest_path)
            }

        except Exception as e:
            self.logger.error(f"Error copying file {source} to {destination}: {e}")
            return {
                "success": False,
                "error": f"Failed to copy file: {str(e)}"
            }

    async def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Move a file"""
        try:
            if not self.is_initialized:
                await self.initialize()

            if not self._is_path_safe(source) or not self._is_path_safe(destination):
                return {
                    "success": False,
                    "error": "Access to one or both paths is not allowed for security reasons"
                }

            source_path = self.base_path / source
            dest_path = self.base_path / destination

            if not source_path.exists():
                return {
                    "success": False,
                    "error": f"Source file '{source}' not found"
                }

            if not source_path.is_file():
                return {
                    "success": False,
                    "error": f"'{source}' is not a file"
                }

            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            shutil.move(str(source_path), str(dest_path))

            self.logger.info(f"File moved: {source} -> {destination}")
            return {
                "success": True,
                "message": f"File '{source}' moved to '{destination}' successfully",
                "source_path": str(source_path),
                "destination_path": str(dest_path)
            }

        except Exception as e:
            self.logger.error(f"Error moving file {source} to {destination}: {e}")
            return {
                "success": False,
                "error": f"Failed to move file: {str(e)}"
            }

    async def search_files(self, pattern: str, directory: str = ".") -> Dict[str, Any]:
        """Search for files matching a pattern"""
        try:
            if not self.is_initialized:
                await self.initialize()

            if not self._is_path_safe(directory):
                return {
                    "success": False,
                    "error": f"Access to path '{directory}' is not allowed for security reasons"
                }

            dir_path = self.base_path / directory
            if not dir_path.exists():
                return {
                    "success": False,
                    "error": f"Directory '{directory}' not found"
                }

            if not dir_path.is_dir():
                return {
                    "success": False,
                    "error": f"'{directory}' is not a directory"
                }

            # Search for files
            matches = []
            for file_path in dir_path.rglob(pattern):
                if file_path.is_file() and self._is_path_safe(str(file_path)):
                    # Get relative path from base
                    rel_path = file_path.relative_to(self.base_path)
                    matches.append(str(rel_path))

            self.logger.info(f"File search completed: {pattern} in {directory} found {len(matches)} matches")
            return {
                "success": True,
                "pattern": pattern,
                "directory": directory,
                "matches": sorted(matches),
                "count": len(matches)
            }

        except Exception as e:
            self.logger.error(f"Error searching files for pattern {pattern} in {directory}: {e}")
            return {
                "success": False,
                "error": f"Failed to search files: {str(e)}"
            }

    async def organize_directory(self, directory: str = ".") -> Dict[str, Any]:
        """
        Organize a directory by grouping loose files into extension folders
        (IMAGES, DOCUMENTS, VIDEO, AUDIO, ARCHIVES, CODE, OTHER).
        """
        try:
            if not self.is_initialized:
                await self.initialize()

            if not self._is_path_safe(directory):
                return {
                    "success": False,
                    "error": f"Access to path '{directory}' is not allowed for security reasons"
                }

            dir_path = self.base_path / directory
            if not dir_path.exists() or not dir_path.is_dir():
                return {
                    "success": False,
                    "error": f"Directory '{directory}' not found"
                }

            groups = {
                "IMAGES": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp", ".svg", ".ico"},
                "DOCUMENTS": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md", ".rtf", ".odt"},
                "VIDEO": {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"},
                "AUDIO": {".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a"},
                "ARCHIVES": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".iso"},
                "CODE": {".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".json", ".xml",
                         ".yaml", ".yml", ".sql", ".sh", ".ps1", ".bat", ".cmd", ".java", ".c",
                         ".cpp", ".h", ".go", ".rs", ".php", ".rb"},
            }

            moved = {}
            for item in dir_path.iterdir():
                if not item.is_file():
                    continue
                ext = item.suffix.lower()
                group_name = "OTHER"
                for g, exts in groups.items():
                    if ext in exts:
                        group_name = g
                        break
                target_dir = dir_path / group_name
                target_dir.mkdir(exist_ok=True)
                destination = target_dir / item.name
                if destination.exists():
                    destination = target_dir / f"{item.stem}_{int(time.time())}{ext}"
                item.replace(destination)
                moved[group_name] = moved.get(group_name, 0) + 1

            if not moved:
                return {
                    "success": True,
                    "message": "No loose files to organize",
                    "moved": 0,
                    "summary": {}
                }

            summary = {k: v for k, v in sorted(moved.items(), key=lambda x: -x[1])}
            total = sum(moved.values())
            self.logger.info(f"Organized {total} files in {directory}: {summary}")
            return {
                "success": True,
                "message": f"Organized {total} files into {len(moved)} categories",
                "moved": total,
                "directory": str(dir_path),
                "summary": summary
            }

        except Exception as e:
            self.logger.error(f"Error organizing directory {directory}: {e}")
            return {
                "success": False,
                "error": f"Failed to organize directory: {str(e)}"
            }

    async def get_file_info(self, filename: str) -> Dict[str, Any]:
        """Get information about a file"""
        try:
            if not self.is_initialized:
                await self.initialize()

            if not self._is_path_safe(filename):
                return {
                    "success": False,
                    "error": f"Access to path '{filename}' is not allowed for security reasons"
                }

            file_path = self.base_path / filename
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File '{filename}' not found"
                }

            stat = file_path.stat()

            self.logger.info(f"File info retrieved: {filename}")
            return {
                "success": True,
                "file_path": str(file_path),
                "name": file_path.name,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
                "is_file": file_path.is_file(),
                "is_directory": file_path.is_dir(),
                "extension": file_path.suffix.lower()
            }

        except Exception as e:
            self.logger.error(f"Error getting file info for {filename}: {e}")
            return {
                "success": False,
                "error": f"Failed to get file info: {str(e)}"
            }

    async def shutdown(self):
        """Shutdown the file system tool"""
        self.logger.info("Shutting down File System Tool")
        self.is_initialized = False