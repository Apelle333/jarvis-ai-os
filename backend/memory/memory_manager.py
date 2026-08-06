"""
JARVIS AI Operating System - Memory Manager
Coordinates short-term and long-term memory systems
"""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from .sqlite_memory import SQLiteMemory
from .vector_memory import VectorMemory

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Memory Manager - Coordinates short-term (SQLite) and long-term (Vector) memory
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        self.sqlite_memory: Optional[SQLiteMemory] = None
        self.vector_memory: Optional[VectorMemory] = None

        # Configuration (override via environment variables)
        self.short_term_limit = int(os.getenv('JARVIS_MEMORY_SHORT_TERM_LIMIT', '1000'))  # Max short-term memories
        self.retention_days = int(os.getenv('JARVIS_MEMORY_RETENTION_DAYS', '30'))  # Days to keep before archiving
        self.long_term_threshold = float(os.getenv('JARVIS_MEMORY_LONG_TERM_THRESHOLD', str(0.7)))  # Similarity threshold for long-term storage
        self.consolidation_interval = int(os.getenv('JARVIS_MEMORY_CONSOLIDATION_INTERVAL', '3600'))  # seconds (1 hour)
        self.last_consolidation = datetime.now()
        self._consolidation_task: Optional[asyncio.Task] = None

        # Memory types
        self.memory_types = {
            "conversation": "conversation",
            "knowledge": "knowledge",
            "preference": "preference",
            "skill": "skill",
            "event": "event",
            "task": "task"
        }

    async def initialize(self):
        """Initialize the memory systems"""
        if self.is_initialized:
            self.logger.info("Memory Manager already initialized")
            return

        try:
            self.logger.info("Initializing Memory Manager...")
            self.sqlite_memory = SQLiteMemory()
            self.vector_memory = VectorMemory()

            await self.sqlite_memory.initialize()

            try:
                await self.vector_memory.initialize()
            except Exception as vector_error:
                self.logger.warning(
                    "Vector memory failed to initialize (continuing with SQLite only): %s",
                    vector_error,
                )

            self.is_initialized = True
            self.logger.info("Memory Manager initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Memory Manager: {e}")
            raise

    async def store_conversation(
        self,
        role: str,
        content: str,
        modality: str = "text",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a conversation entry in short-term memory

        Args:
            role: 'user' or 'assistant'
            content: The conversation content
            modality: 'text', 'voice', 'vision', etc.
            timestamp: When the conversation occurred
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        if not self.is_initialized:
            await self.initialize()

        if timestamp is None:
            timestamp = datetime.now()

        if metadata is None:
            metadata = {}

        # Store in short-term memory
        memory_id = await self.sqlite_memory.store_conversation(
            role=role,
            content=content,
            modality=modality,
            timestamp=timestamp,
            metadata=metadata
        )

        # Check if this should be consolidated to long-term memory
        await self._check_consolidation(
            memory_type="conversation",
            content=content,
            metadata={
                "role": role,
                "modality": modality,
                "memory_id": memory_id,
                **metadata
            }
        )

        return memory_id

    async def store_knowledge(
        self,
        title: str,
        content: str,
        source: str = "unknown",
        tags: Optional[List[str]] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store knowledge in long-term memory

        Args:
            title: Title of the knowledge
            content: The knowledge content
            source: Source of the knowledge
            tags: Tags for categorization
            timestamp: When the knowledge was acquired
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        if not self.is_initialized:
            await self.initialize()

        if timestamp is None:
            timestamp = datetime.now()

        if tags is None:
            tags = []

        if metadata is None:
            metadata = {}

        # Store in long-term memory
        memory_id = await self.vector_memory.store_knowledge(
            title=title,
            content=content,
            source=source,
            tags=tags,
            timestamp=timestamp,
            metadata=metadata
        )

        return memory_id

    async def store_preference(
        self,
        key: str,
        value: Any,
        category: str = "general",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a user preference

        Args:
            key: Preference key
            value: Preference value
            category: Category of preference
            timestamp: When the preference was set
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        if not self.is_initialized:
            await self.initialize()

        if timestamp is None:
            timestamp = datetime.now()

        if metadata is None:
            metadata = {}

        content = f"{key}: {json.dumps(value) if not isinstance(value, str) else value}"

        # Store in both short-term (for quick access) and long-term
        short_term_id = await self.sqlite_memory.store_preference(
            key=key,
            value=value,
            category=category,
            timestamp=timestamp,
            metadata=metadata
        )

        long_term_id = await self.vector_memory.store_preference(
            key=key,
            value=value,
            category=category,
            timestamp=timestamp,
            metadata=metadata
        )

        return f"{short_term_id}:{long_term_id}"

    async def store_skill(
        self,
        name: str,
        description: str,
        proficiency: float = 0.0,
        category: str = "general",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a skill or ability

        Args:
            name: Skill name
            description: Skill description
            proficiency: Proficiency level (0.0 to 1.0)
            category: Skill category
            timestamp: When the skill was learned/updated
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        if not self.is_initialized:
            await self.initialize()

        if timestamp is None:
            timestamp = datetime.now()

        if metadata is None:
            metadata = {}

        content = f"Skill: {name}. Description: {description}. Proficiency: {proficiency}"

        # Store in long-term memory
        memory_id = await self.vector_memory.store_skill(
            name=name,
            description=description,
            proficiency=proficiency,
            category=category,
            timestamp=timestamp,
            metadata=metadata
        )

        return memory_id

    async def store_event(
        self,
        title: str,
        description: str,
        event_type: str = "general",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        location: Optional[str] = None,
        participants: Optional[List[str]] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store an event or reminder

        Args:
            title: Event title
            description: Event description
            event_type: Type of event
            start_time: When the event starts
            end_time: When the event ends
            location: Where the event occurs
            participants: Who is involved
            timestamp: When the event was recorded
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        if not self.is_initialized:
            await self.initialize()

        if timestamp is None:
            timestamp = datetime.now()

        if metadata is None:
            metadata = {}

        content = f"Event: {title}. Description: {description}"

        if start_time:
            content += f". Start: {start_time.isoformat()}"
        if end_time:
            content += f". End: {end_time.isoformat()}"
        if location:
            content += f". Location: {location}"
        if participants:
            content += f". Participants: {', '.join(participants)}"

        # Store in both short-term (for recent events) and long-term
        short_term_id = await self.sqlite_memory.store_event(
            title=title,
            description=description,
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            location=location,
            participants=participants,
            timestamp=timestamp,
            metadata=metadata
        )

        long_term_id = await self.vector_memory.store_event(
            title=title,
            description=description,
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            location=location,
            participants=participants,
            timestamp=timestamp,
            metadata=metadata
        )

        return f"{short_term_id}:{long_term_id}"

    async def store_task(
        self,
        title: str,
        description: str,
        status: str = "pending",
        priority: int = 1,  # 1=low, 2=medium, 3=high
        due_date: Optional[datetime] = None,
        assigned_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a task or to-do item

        Args:
            title: Task title
            description: Task description
            status: Current status
            priority: Priority level
            due_date: When the task is due
            assigned_to: Who the task is assigned to
            tags: Tags for categorization
            timestamp: When the task was created
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        if not self.is_initialized:
            await self.initialize()

        if timestamp is None:
            timestamp = datetime.now()

        if tags is None:
            tags = []

        if metadata is None:
            metadata = {}

        content = f"Task: {title}. Description: {description}. Status: {status}. Priority: {priority}"

        if due_date:
            content += f". Due: {due_date.isoformat()}"
        if assigned_to:
            content += f". Assigned to: {assigned_to}"
        if tags:
            content += f". Tags: {', '.join(tags)}"

        # Store in both short-term (for active tasks) and long-term
        short_term_id = await self.sqlite_memory.store_task(
            title=title,
            description=description,
            status=status,
            priority=priority,
            due_date=due_date,
            assigned_to=assigned_to,
            tags=tags,
            timestamp=timestamp,
            metadata=metadata
        )

        long_term_id = await self.vector_memory.store_task(
            title=title,
            description=description,
            status=status,
            priority=priority,
            due_date=due_date,
            assigned_to=assigned_to,
            tags=tags,
            timestamp=timestamp,
            metadata=metadata
        )

        return f"{short_term_id}:{long_term_id}"

    async def get_recent_context(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversation context from short-term memory

        Args:
            limit: Maximum number of items to return

        Returns:
            List of recent conversation items
        """
        if not self.is_initialized:
            await self.initialize()

        return await self.sqlite_memory.get_recent_conversations(limit=limit)

    async def search_memory(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search across both short-term and long-term memory

        Args:
            query: Search query
            memory_type: Type of memory to search (None for all)
            limit: Maximum results to return
            min_similarity: Minimum similarity score (0.0 to 1.0)

        Returns:
            List of matching memory items
        """
        if not self.is_initialized:
            await self.initialize()

        results = []

        # Search short-term memory
        short_term_results = await self.sqlite_memory.search(
            query=query,
            memory_type=memory_type,
            limit=limit
        )
        results.extend(short_term_results)

        # Search long-term memory
        long_term_results = await self.vector_memory.search(
            query=query,
            limit=limit,
            min_similarity=min_similarity
        )
        results.extend(long_term_results)

        # Sort by relevance/score and limit
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return results[:limit]

    async def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific memory by ID

        Args:
            memory_id: The memory ID (may be compound for dual-storage items)

        Returns:
            Memory data or None if not found
        """
        if not self.is_initialized:
            await self.initialize()

        # Check if this is a compound ID (short_term:long_term)
        if ':' in memory_id:
            short_id, long_id = memory_id.split(':', 1)
            # Try short-term first (more likely to be recent)
            result = await self.sqlite_memory.get_by_id(short_id)
            if result:
                return result
            # Fall back to long-term
            return await self.vector_memory.get_by_id(long_id)
        else:
            # Try both memory systems
            result = await self.sqlite_memory.get_by_id(memory_id)
            if result:
                return result
            return await self.vector_memory.get_by_id(memory_id)

    async def update_memory(
        self,
        memory_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update a memory entry

        Args:
            memory_id: The memory ID to update
            updates: Dictionary of fields to update

        Returns:
            True if successful
        """
        if not self.is_initialized:
            await self.initialize()

        # Check if this is a compound ID
        if ':' in memory_id:
            short_id, long_id = memory_id.split(':', 1)
            # Update both if they exist
            short_result = await self.sqlite_memory.update_by_id(short_id, updates)
            long_result = await self.vector_memory.update_by_id(long_id, updates)
            return short_result or long_result
        else:
            # Try short-term first
            result = await self.sqlite_memory.update_by_id(memory_id, updates)
            if not result:
                # Try long-term
                result = await self.vector_memory.update_by_id(memory_id, updates)
            return result

    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory entry

        Args:
            memory_id: The memory ID to delete

        Returns:
            True if successful
        """
        if not self.is_initialized:
            await self.initialize()

        # Check if this is a compound ID
        if ':' in memory_id:
            short_id, long_id = memory_id.split(':', 1)
            # Delete from both
            short_result = await self.sqlite_memory.delete_by_id(short_id)
            long_result = await self.vector_memory.delete_by_id(long_id)
            return short_result or long_result
        else:
            # Try short-term first
            result = await self.sqlite_memory.delete_by_id(memory_id)
            if not result:
                # Try long-term
                result = await self.vector_memory.delete_by_id(memory_id)
            return result

    async def consolidate_memories(self) -> Dict[str, Any]:
        """
        Consolidate short-term memories to long-term memory based on importance

        Returns:
            Statistics about the consolidation process
        """
        if not self.is_initialized:
            await self.initialize()

        stats = {
            "consolidated": 0,
            "skipped": 0,
            "errors": 0,
            "start_time": datetime.now().isoformat()
        }

        try:
            # Get candidates for consolidation from short-term memory
            candidates = await self.sqlite_memory.get_consolidation_candidates(
                limit=100,
                min_age_minutes=30  # Only consider items older than 30 minutes
            )

            for candidate in candidates:
                try:
                    # Determine if this should be moved to long-term memory
                    should_consolidate = await self._should_consolidate(candidate)

                    if should_consolidate:
                        # Store in long-term memory
                        await self._store_in_long_term(candidate)
                        # Mark as consolidated in short-term (or remove if configured)
                        await self.sqlite_memory.mark_as_consolidated(candidate["id"])
                        stats["consolidated"] += 1
                    else:
                        stats["skipped"] += 1

                except Exception as e:
                    self.logger.error(f"Error consolidating memory {candidate.get('id')}: {e}")
                    stats["errors"] += 1

            self.last_consolidation = datetime.now()
            stats["end_time"] = self.last_consolidation.isoformat()

            self.logger.info(f"Memory consolidation completed: {stats}")
            return stats

        except Exception as e:
            self.logger.error(f"Error during memory consolidation: {e}", exc_info=True)
            stats["error"] = str(e)
            return stats

    async def prune_short_term(self) -> Dict[str, Any]:
        """Prune short-term memory to configured limits and by retention days.

        This archives old items (via SQLiteMemory) and never permanently deletes user data.
        """
        if not self.is_initialized:
            await self.initialize()

        stats = {"pruned": 0, "details": {}, "retention_days": self.retention_days, "limit": self.short_term_limit}
        try:
            # Archive items older than retention_days
            cutoff = datetime.now() - timedelta(days=self.retention_days)
            arch_res = await self.sqlite_memory.clear_old_memories(cutoff)
            stats["details"]["archived_by_age"] = arch_res.get("details", {}) if isinstance(arch_res, dict) else {}

            # Prune to short_term_limit
            prune_res = await self.sqlite_memory.prune_to_limit(self.short_term_limit)
            stats["details"]["pruned_to_limit"] = prune_res
            stats["pruned"] = prune_res.get("moved", 0) if isinstance(prune_res, dict) else 0

            return stats
        except Exception as e:
            self.logger.error(f"Error pruning short-term memories: {e}")
            stats["error"] = str(e)
            return stats

    async def _should_consolidate(self, memory_item: Dict[str, Any]) -> bool:
        """
        Determine if a memory item should be consolidated to long-term memory

        Args:
            memory_item: The memory item to evaluate

        Returns:
            True if should be consolidated
        """
        # Simple heuristic - in production would use more sophisticated scoring
        content = memory_item.get("content", "")
        metadata = memory_item.get("metadata", {})

        # Don't consolidate very short items
        if len(content.strip()) < 20:
            return False

        # Consolidate items with certain metadata flags
        if metadata.get("important", False):
            return True

        # Consolidate user preferences and learned information
        if memory_item.get("type") in ["preference", "skill", "knowledge"]:
            return True

        # Consolidate items that have been referenced multiple times
        reference_count = metadata.get("reference_count", 0)
        if reference_count > 3:
            return True

        # For conversation items, consolidate if they contain useful information
        if memory_item.get("type") == "conversation":
            # Look for indicators of useful information
            indicators = [
                "how to", "what is", "why", "explain", "define",
                "remember", "important", "note", "tip", "advice",
                "learn", "understand", "example", "solution"
            ]
            content_lower = content.lower()
            if any(indicator in content_lower for indicator in indicators):
                return True

        # Default: consolidate older items with moderate frequency
        age_minutes = memory_item.get("age_minutes", 0)
        if age_minutes > 60:  # Older than 1 hour
            return True

        return False

    async def _store_in_long_term(self, memory_item: Dict[str, Any]):
        """
        Store a memory item in long-term memory

        Args:
            memory_item: The memory item to store
        """
        memory_type = memory_item.get("type", "unknown")
        content = memory_item.get("content", "")
        metadata = memory_item.get("metadata", {})
        timestamp = memory_item.get("timestamp", datetime.now())

        # Convert timestamp if it's a string
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except:
                timestamp = datetime.now()

        # Store based on type
        if memory_type == "conversation":
            role = metadata.get("role", "unknown")
            await self.store_conversation(
                role=role,
                content=content,
                modality=metadata.get("modality", "text"),
                timestamp=timestamp,
                metadata={**metadata, "consolidated": True}
            )
        elif memory_type == "preference":
            key = metadata.get("key", "unknown")
            value = metadata.get("value", "")
            await self.store_preference(
                key=key,
                value=value,
                category=metadata.get("category", "general"),
                timestamp=timestamp,
                metadata={**metadata, "consolidated": True}
            )
        elif memory_type == "skill":
            name = metadata.get("name", "Unknown Skill")
            description = metadata.get("description", "")
            proficiency = float(metadata.get("proficiency", 0.0))
            await self.store_skill(
                name=name,
                description=description,
                proficiency=proficiency,
                category=metadata.get("category", "general"),
                timestamp=timestamp,
                metadata={**metadata, "consolidated": True}
            )
        elif memory_type == "event":
            await self.store_event(
                title=metadata.get("title", "Untitled Event"),
                description=content,
                event_type=metadata.get("event_type", "general"),
                start_time=metadata.get("start_time"),
                end_time=metadata.get("end_time"),
                location=metadata.get("location"),
                participants=metadata.get("participants"),
                timestamp=timestamp,
                metadata={**metadata, "consolidated": True}
            )
        elif memory_type == "task":
            await self.store_task(
                title=metadata.get("title", "Untitled Task"),
                description=content,
                status=metadata.get("status", "pending"),
                priority=int(metadata.get("priority", 1)),
                due_date=metadata.get("due_date"),
                assigned_to=metadata.get("assigned_to"),
                tags=metadata.get("tags", []),
                timestamp=timestamp,
                metadata={**metadata, "consolidated": True}
            )
        else:
            # Generic knowledge storage
            title = metadata.get("title", f"Memory from {timestamp.strftime('%Y-%m-%d %H:%M')}")
            await self.store_knowledge(
                title=title,
                content=content,
                source=metadata.get("source", "consolidation"),
                tags=metadata.get("tags", []),
                timestamp=timestamp,
                metadata={**metadata, "consolidated": True}
            )

    async def _check_consolidation(self, memory_type: str, content: str, metadata: Dict[str, Any]):
        """
        Check if a newly stored item should trigger consolidation

        Args:
            memory_type: Type of memory
            content: Content of the memory
            metadata: Metadata associated with the memory
        """
        # Check if it's time for periodic consolidation
        now = datetime.now()
        if (now - self.last_consolidation).total_seconds() <= self.consolidation_interval:
            return

        # Consolidation may index many older records. Schedule only one run at
        # a time and advance the interval before it starts, otherwise each new
        # chat turn can enqueue another expensive maintenance job.
        if self._consolidation_task is not None and not self._consolidation_task.done():
            return

        self.last_consolidation = now
        self._consolidation_task = asyncio.create_task(self.consolidate_memories())

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        if not self.is_initialized:
            await self.initialize()

        sqlite_stats = await self.sqlite_memory.get_stats()
        vector_stats = await self.vector_memory.get_stats()

        # Archive counts (if available)
        try:
            archive_counts = await self.sqlite_memory.get_archive_counts()
        except Exception:
            archive_counts = {}

        # Vector fallback flag
        chroma_available = bool(vector_stats.get("chromadb_available", True))
        fallback_count = int(vector_stats.get("fallback_count", 0)) if isinstance(vector_stats, dict) else 0

        return {
            "short_term": sqlite_stats,
            "long_term": vector_stats,
            "archive_counts": archive_counts,
            "chroma_available": chroma_available,
            "vector_fallback_count": fallback_count,
            "last_consolidation": self.last_consolidation.isoformat() if self.last_consolidation else None,
            "consolidation_interval_seconds": self.consolidation_interval,
            "is_initialized": self.is_initialized
        }

    async def clear_old_memories(self, days: int = 30) -> Dict[str, Any]:
        """
        Clear memories older than specified days

        Args:
            days: Number of days to keep

        Returns:
            Statistics about the cleanup
        """
        if not self.is_initialized:
            await self.initialize()

        cutoff_date = datetime.now() - timedelta(days=days)

        # Clear from both memory systems
        sqlite_result = await self.sqlite_memory.clear_old_memories(cutoff_date)
        vector_result = await self.vector_memory.clear_old_memories(cutoff_date)

        return {
            "short_term": sqlite_result,
            "long_term": vector_result,
            "cutoff_date": cutoff_date.isoformat()
        }

    async def shutdown(self):
        """Shutdown the memory systems"""
        self.logger.info("Shutting down Memory Manager")
        self.is_initialized = False

        if self.sqlite_memory:
            await self.sqlite_memory.shutdown()
        if self.vector_memory:
            await self.vector_memory.shutdown()
