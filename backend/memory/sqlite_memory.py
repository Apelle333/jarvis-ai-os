"""
JARVIS AI Operating System - SQLite Memory
Short-term memory storage using SQLite
"""

import asyncio
import logging
import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import aiosqlite

logger = logging.getLogger(__name__)


class SQLiteMemory:
    """
    SQLite Memory - Short-term memory storage
    """

    def __init__(self, db_path: str = "./database/jarvis_memory.db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None
        self.is_initialized = False

    async def initialize(self):
        """Initialize the SQLite database and tables"""
        try:
            self.logger.info(f"Initializing SQLite memory at {self.db_path}...")

            # Ensure directory exists
            import os
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            # Create connection
            self.connection = await aiosqlite.connect(self.db_path)

            # Enable foreign keys
            await self.connection.execute("PRAGMA foreign_keys = ON")

            # Create tables
            await self._create_tables()

            self.is_initialized = True
            self.logger.info("SQLite memory initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize SQLite memory: {e}")
            raise

    async def _create_tables(self):
        """Create database tables"""
        # Conversations table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                modality TEXT DEFAULT 'text',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,  -- JSON stored as text
                is_consolidated BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Preferences table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,  -- JSON stored as text
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Events table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                event_type TEXT DEFAULT 'general',
                start_time DATETIME,
                end_time DATETIME,
                location TEXT,
                participants TEXT,  -- JSON array
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,  -- JSON stored as text
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tasks table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 1,
                due_date DATETIME,
                assigned_to TEXT,
                tags TEXT,  -- JSON array
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,  -- JSON stored as text
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for better performance
        await self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_timestamp
            ON conversations(timestamp)
        """)

        await self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_role
            ON conversations(role)
        """)

        await self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_preferences_key
            ON preferences(key)
        """)

        await self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_timestamp
            ON events(timestamp)
        """)

        await self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status
            ON tasks(status)
        """)

        await self.connection.commit()

    async def store_conversation(
        self,
        role: str,
        content: str,
        modality: str = "text",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Store a conversation entry"""
        if not self.is_initialized:
            await self.initialize()

        if timestamp is None:
            timestamp = datetime.now()
        if metadata is None:
            metadata = {}

        cursor = await self.connection.execute("""
            INSERT INTO conversations (role, content, modality, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            role,
            content,
            modality,
            timestamp.isoformat(),
            json.dumps(metadata)
        ))

        await self.connection.commit()
        return cursor.lastrowid

    async def store_preference(
        self,
        key: str,
        value: Any,
        category: str = "general",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Store a preference"""
        if not self.is_initialized:
            await self.initialize()

        if timestamp is None:
            timestamp = datetime.now()
        if metadata is None:
            metadata = {}

        # Convert value to JSON string for storage
        value_str = json.dumps(value) if not isinstance(value, str) else value

        cursor = await self.connection.execute("""
            INSERT INTO preferences (key, value, category, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            key,
            value_str,
            category,
            timestamp.isoformat(),
            json.dumps(metadata)
        ))

        await self.connection.commit()
        return cursor.lastrowid

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
    ) -> int:
        """Store an event"""
        if not self.is_initialized:
            await self.initialize()

        if timestamp is None:
            timestamp = datetime.now()
        if metadata is None:
            metadata = {}
        if participants is None:
            participants = []

        cursor = await self.connection.execute("""
            INSERT INTO events
            (title, description, event_type, start_time, end_time, location, participants, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            event_type,
            start_time.isoformat() if start_time else None,
            end_time.isoformat() if end_time else None,
            location,
            json.dumps(participants),
            timestamp.isoformat(),
            json.dumps(metadata)
        ))

        await self.connection.commit()
        return cursor.lastrowid

    async def store_task(
        self,
        title: str,
        description: str,
        status: str = "pending",
        priority: int = 1,
        due_date: Optional[datetime] = None,
        assigned_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Store a task"""
        if not self.is_initialized:
            await self.initialize()

        if timestamp is None:
            timestamp = datetime.now()
        if tags is None:
            tags = []
        if metadata is None:
            metadata = {}

        cursor = await self.connection.execute("""
            INSERT INTO tasks
            (title, description, status, priority, due_date, assigned_to, tags, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            status,
            priority,
            due_date.isoformat() if due_date else None,
            assigned_to,
            json.dumps(tags),
            timestamp.isoformat(),
            json.dumps(metadata)
        ))

        await self.connection.commit()
        return cursor.lastrowid

    async def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations"""
        if not self.is_initialized:
            await self.initialize()

        cursor = await self.connection.execute("""
            SELECT id, role, content, modality, timestamp, metadata, is_consolidated
            FROM conversations
            WHERE is_consolidated = 0
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = await cursor.fetchall()

        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "role": row[1],
                "content": row[2],
                "modality": row[3],
                "timestamp": row[4],
                "metadata": json.loads(row[5]) if row[5] else {},
                "is_consolidated": bool(row[6])
            })

        return results

    async def search(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memory entries"""
        if not self.is_initialized:
            await self.initialize()

        # Build query based on memory type
        if memory_type == "conversation":
            table = "conversations"
            id_col = "id"
            select_cols = "id, role, content, modality, timestamp, metadata, is_consolidated"
            where_conditions = ["(content LIKE ? OR role LIKE ?)"]
            params = [f"%{query}%", f"%{query}%"]
        elif memory_type == "preference":
            table = "preferences"
            id_col = "id"
            select_cols = "id, key, value, category, timestamp, metadata"
            where_conditions = ["(key LIKE ? OR value LIKE ? OR category LIKE ?)"]
            params = [f"%{query}%", f"%{query}%", f"%{query}%"]
        elif memory_type == "event":
            table = "events"
            id_col = "id"
            select_cols = "id, title, description, event_type, start_time, end_time, location, participants, timestamp, metadata"
            where_conditions = ["(title LIKE ? OR description LIKE ? OR event_type LIKE ?)"]
            params = [f"%{query}%", f"%{query}%", f"%{query}%"]
        elif memory_type == "task":
            table = "tasks"
            id_col = "id"
            select_cols = "id, title, description, status, priority, due_date, assigned_to, tags, timestamp, metadata"
            where_conditions = ["(title LIKE ? OR description LIKE ? OR status LIKE ?)"]
            params = [f"%{query}%", f"%{query}%", f"%{query}%"]
        else:
            # Search all tables - we'll do this by querying each table separately
            results = []

            # Search conversations
            conv_results = await self._search_table(
                "conversations",
                "id, role, content, modality, timestamp, metadata, is_consolidated",
                ["content", "role"],
                query,
                limit
            )
            for r in conv_results:
                r["type"] = "conversation"
                results.append(r)

            # Search preferences
            pref_results = await self._search_table(
                "preferences",
                "id, key, value, category, timestamp, metadata",
                ["key", "value", "category"],
                query,
                limit
            )
            for r in pref_results:
                r["type"] = "preference"
                results.append(r)

            # Search events
            event_results = await self._search_table(
                "events",
                "id, title, description, event_type, start_time, end_time, location, participants, timestamp, metadata",
                ["title", "description", "event_type"],
                query,
                limit
            )
            for r in event_results:
                r["type"] = "event"
                results.append(r)

            # Search tasks
            task_results = await self._search_table(
                "tasks",
                "id, title, description, status, priority, due_date, assigned_to, tags, timestamp, metadata",
                ["title", "description", "status"],
                query,
                limit
            )
            for r in task_results:
                r["type"] = "task"
                results.append(r)

            # Sort by timestamp and limit
            results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return results[:limit]

        # Execute query for single table type
        column_map = {
            "conversation": ["content", "role"],
            "preference": ["key", "value", "category"],
            "event": ["title", "description", "event_type"],
            "task": ["title", "description", "status"],
        }
        search_columns = column_map.get(memory_type, ["content", "title", "description"])

        results = await self._search_table(
            table,
            select_cols,
            search_columns,
            query,
            limit
        )

        # Add type information
        for r in results:
            r["type"] = memory_type

        return results

    async def _search_table(
        self,
        table: str,
        select_cols: str,
        search_columns: List[str],
        query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Helper to search a specific table"""
        # Build LIKE conditions
        like_conditions = []
        params = []
        for col in search_columns:
            like_conditions.append(f"{col} LIKE ?")
            params.append(f"%{query}%")

        where_clause = " OR ".join(like_conditions)

        sql = f"""
            SELECT {select_cols}
            FROM {table}
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """
        params.append(limit)

        cursor = await self.connection.execute(sql, tuple(params))
        rows = await cursor.fetchall()

        # Convert rows to dictionaries
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in rows:
            result = dict(zip(columns, row))
            # Parse JSON fields
            if "metadata" in result and result["metadata"]:
                try:
                    result["metadata"] = json.loads(result["metadata"])
                except:
                    result["metadata"] = {}
            results.append(result)

        return results

    async def get_by_id(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """Get a memory by ID (checks all tables)"""
        if not self.is_initialized:
            await self.initialize()

        # Try conversations first
        table_order = ["conversations", "preferences", "events", "tasks"]
        for table in table_order:
            result = await self._get_from_table_by_id(table, memory_id)
            if result:
                result["type"] = table
                return result

        return None

    async def _get_from_table_by_id(self, table: str, memory_id: int) -> Optional[Dict[str, Any]]:
        """Get a record by ID from a specific table"""
        if not self.is_initialized:
            await self.initialize()

        # Define columns for each table
        table_columns = {
            "conversations": "id, role, content, modality, timestamp, metadata, is_consolidated",
            "preferences": "id, key, value, category, timestamp, metadata",
            "events": "id, title, description, event_type, start_time, end_time, location, participants, timestamp, metadata",
            "tasks": "id, title, description, status, priority, due_date, assigned_to, tags, timestamp, metadata"
        }

        if table not in table_columns:
            return None

        select_cols = table_columns[table]

        cursor = await self.connection.execute(
            f"SELECT {select_cols} FROM {table} WHERE id = ?",
            (memory_id,)
        )
        row = await cursor.fetchone()

        if row:
            columns = [desc[0] for desc in cursor.description]
            result = dict(zip(columns, row))
            # Parse JSON fields
            if "metadata" in result and result["metadata"]:
                try:
                    result["metadata"] = json.loads(result["metadata"])
                except:
                    result["metadata"] = {}
            # Parse special fields
            if "participants" in result and result["participants"]:
                try:
                    result["participants"] = json.loads(result["participants"])
                except:
                    result["participants"] = []
            if "tags" in result and result["tags"]:
                try:
                    result["tags"] = json.loads(result["tags"])
                except:
                    result["tags"] = []
            return result

        return None

    async def update_by_id(self, memory_id: int, updates: Dict[str, Any]) -> bool:
        """Update a record by ID"""
        if not self.is_initialized:
            await self.initialize()

        # Determine which table the ID belongs to by checking each
        table_order = ["conversations", "preferences", "events", "tasks"]
        for table in table_order:
            exists = await self._record_exists(table, memory_id)
            if exists:
                return await self._update_table_by_id(table, memory_id, updates)

        return False

    async def _record_exists(self, table: str, memory_id: int) -> bool:
        """Check if a record exists in a table"""
        if not self.is_initialized:
            await self.initialize()

        cursor = await self.connection.execute(
            f"SELECT 1 FROM {table} WHERE id = ? LIMIT 1",
            (memory_id,)
        )
        row = await cursor.fetchone()
        return row is not None

    async def _update_table_by_id(self, table: str, memory_id: int, updates: Dict[str, Any]) -> bool:
        """Update a record in a specific table"""
        if not self.is_initialized:
            await self.initialize()

        # Define updatable fields for each table
        updatable_fields = {
            "conversations": ["role", "content", "modality", "metadata", "is_consolidated"],
            "preferences": ["key", "value", "category", "metadata"],
            "events": ["title", "description", "event_type", "start_time", "end_time", "location", "participants", "metadata"],
            "tasks": ["title", "description", "status", "priority", "due_date", "assigned_to", "tags", "metadata"]
        }

        if table not in updatable_fields:
            return False

        # Filter updates to only allowed fields
        allowed_updates = {k: v for k, v in updates.items() if k in updatable_fields[table]}
        if not allowed_updates:
            return False

        # Prepare SET clause
        set_clauses = []
        params = []
        for key, value in allowed_updates.items():
            if key in ["metadata", "participants", "tags"] and isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif key in ["start_time", "end_time", "due_date", "timestamp"] and isinstance(value, datetime):
                value = value.isoformat()
            set_clauses.append(f"{key} = ?")
            params.append(value)

        if not set_clauses:
            return False

        # Add the ID parameter
        params.append(memory_id)

        # Execute update
        sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE id = ?"
        cursor = await self.connection.execute(sql, tuple(params))
        await self.connection.commit()

        return cursor.rowcount > 0

    async def delete_by_id(self, memory_id: int) -> bool:
        """Delete a record by ID"""
        if not self.is_initialized:
            await self.initialize()

        # Try each table
        table_order = ["conversations", "preferences", "events", "tasks"]
        for table in table_order:
            exists = await self._record_exists(table, memory_id)
            if exists:
                return await self._delete_from_table_by_id(table, memory_id)

        return False

    async def _delete_from_table_by_id(self, table: str, memory_id: int) -> bool:
        """Delete a record from a specific table"""
        if not self.is_initialized:
            await self.initialize()

        cursor = await self.connection.execute(
            f"DELETE FROM {table} WHERE id = ?",
            (memory_id,)
        )
        await self.connection.commit()
        return cursor.rowcount > 0

    async def get_consolidation_candidates(
        self,
        limit: int = 100,
        min_age_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """Get candidates for consolidation to long-term memory"""
        if not self.is_initialized:
            await self.initialize()

        cutoff_time = datetime.now() - timedelta(minutes=min_age_minutes)

        cursor = await self.connection.execute("""
            SELECT id, role, content, modality, timestamp, metadata, is_consolidated
            FROM conversations
            WHERE is_consolidated = 0
              AND timestamp < ?
            ORDER BY timestamp ASC
            LIMIT ?
        """, (cutoff_time.isoformat(), limit))

        rows = await cursor.fetchall()

        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "type": "conversation",
                "role": row[1],
                "content": row[2],
                "modality": row[3],
                "timestamp": row[4],
                "metadata": json.loads(row[5]) if row[5] else {},
                "is_consolidated": bool(row[6]),
                "age_minutes": (datetime.now() - datetime.fromisoformat(row[4])).total_seconds() / 60
            })

        return results

    async def mark_as_consolidated(self, memory_id: int) -> bool:
        """Mark a conversation as consolidated"""
        if not self.is_initialized:
            await self.initialize()

        cursor = await self.connection.execute(
            "UPDATE conversations SET is_consolidated = 1 WHERE id = ?",
            (memory_id,)
        )
        await self.connection.commit()
        return cursor.rowcount > 0

    async def clear_old_memories(self, cutoff_date: datetime) -> Dict[str, Any]:
        """Clear memories older than cutoff date"""
        if not self.is_initialized:
            await self.initialize()

        cutoff_str = cutoff_date.isoformat()

        tables = ["conversations", "preferences", "events", "tasks"]
        results = {}

        for table in tables:
            cursor = await self.connection.execute(
                f"DELETE FROM {table} WHERE timestamp < ?",
                (cutoff_str,)
            )
            await self.connection.commit()
            results[table] = cursor.rowcount

        return {
            "deleted_count": sum(results.values()),
            "details": results,
            "cutoff_date": cutoff_str
        }

    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self.is_initialized:
            await self.initialize()

        stats = {}

        # Get counts for each table
        tables = ["conversations", "preferences", "events", "tasks"]
        for table in tables:
            cursor = await self.connection.execute(f"SELECT COUNT(*) FROM {table}")
            count = (await cursor.fetchone())[0]
            stats[f"{table}_count"] = count

            # Get consolidated count for conversations
            if table == "conversations":
                cursor = await self.connection.execute(
                    "SELECT COUNT(*) FROM conversations WHERE is_consolidated = 1"
                )
                consolidated_count = (await cursor.fetchone())[0]
                stats["conversations_consolidated"] = consolidated_count
                stats["conversations_active"] = count - consolidated_count

        # Get database size
        cursor = await self.connection.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        size_row = await cursor.fetchone()
        db_size = size_row[0] if size_row else 0

        stats["database_size_bytes"] = db_size
        stats["database_size_mb"] = round(db_size / (1024 * 1024)) if db_size else 0

        return stats

    async def shutdown(self):
        """Close the database connection"""
        self.logger.info("Shutting down SQLite memory")
        self.is_initialized = False
        if self.connection:
            await self.connection.close()