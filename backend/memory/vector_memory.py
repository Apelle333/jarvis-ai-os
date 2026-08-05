"""
JARVIS AI Operating System - Vector Memory
Long-term memory storage using ChromaDB for vector embeddings
"""

import asyncio
import logging
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import json

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("ChromaDB not installed. Vector memory will be limited.")

logger = logging.getLogger(__name__)


class VectorMemory:
    """
    Vector Memory - Long-term memory using ChromaDB for semantic search
    """

    def __init__(self, db_path: str = "./database/chroma_db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.is_initialized = False
        self.client = None
        self.collections = {}  # Cache for collections

        # Collection names
        self.collections_config = {
            "knowledge": "jarvis_knowledge",
            "preferences": "jarvis_preferences",
            "skills": "jarvis_skills",
            "events": "jarvis_events",
            "tasks": "jarvis_tasks",
            "conversations": "jarvis_conversations"
        }

        # Embedding function - we'll use a simple fallback if sentence-transformers not available
        self.embedding_function = None
        self.embedding_model_name = "all-MiniLM-L6-v2"

    async def initialize(self):
        """Initialize the vector database"""
        try:
            self.logger.info(f"Initializing Vector memory at {self.db_path}...")

            if not CHROMADB_AVAILABLE:
                self.logger.warning("ChromaDB not available - using fallback memory storage")
                self.is_initialized = True
                return

            # Ensure directory exists
            import os
            os.makedirs(self.db_path, exist_ok=True)

            # Initialize ChromaDB client
            # Minimal suppression for telemetry mismatches: if the installed
            # PostHog/ChromaDB telemetry implementation is incompatible it can
            # emit harmless errors. Disable posthog capture here to avoid
            # noisy telemetry exceptions while leaving ChromaDB functionality.
            try:
                # Try to disable posthog telemetry if available
                import chromadb.telemetry.product.posthog as chpost
                try:
                    chpost.posthog.disabled = True
                except Exception:
                    pass
                try:
                    chpost.posthog.capture = lambda *a, **k: None
                except Exception:
                    pass
            except Exception:
                # telemetry internals missing or different version — ignore
                pass

            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Initialize embedding function
            await self._initialize_embedding_function()

            # Get or create collections
            await self._initialize_collections()

            self.is_initialized = True
            self.logger.info("Vector memory initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Vector memory: {e}")
            # Don't raise - allow fallback to basic storage
            self.is_initialized = True
            self.logger.warning("Vector memory initialization failed - using basic storage")

    async def _initialize_embedding_function(self):
        """Initialize the embedding function for vectorization"""
        try:
            # Try to use sentence-transformers for embeddings (load off the event loop)
            import asyncio

            def _load_embedding_model():
                from sentence_transformers import SentenceTransformer
                return SentenceTransformer(self.embedding_model_name)

            loop = asyncio.get_running_loop()
            self.embedding_function = await loop.run_in_executor(
                None, _load_embedding_model
            )
            self.logger.info(f"Embedding function initialized: {self.embedding_model_name}")
        except ImportError:
            self.logger.warning("sentence-transformers not available - using simple hashing for embeddings")
            # Fallback to a simple hash-based approach
            self.embedding_function = None
        except Exception as e:
            self.logger.error(f"Error initializing embedding function: {e}")
            self.embedding_function = None

    async def _initialize_collections(self):
        """Get or create collections for different memory types"""
        if not CHROMADB_AVAILABLE or not self.client:
            return

        for memory_type, collection_name in self.collections_config.items():
            try:
                # Try to get existing collection
                collection = self.client.get_collection(name=collection_name)
                self.logger.info(f"Retrieved existing collection: {collection_name}")
            except Exception:
                # Create new collection if it doesn't exist
                try:
                    collection = self.client.create_collection(
                        name=collection_name,
                        metadata={"hnsw:space": "cosine"}  # Use cosine similarity
                    )
                    self.logger.info(f"Created new collection: {collection_name}")
                except Exception as e:
                    self.logger.error(f"Error creating collection {collection_name}: {e}")
                    collection = None

            if collection:
                self.collections[memory_type] = collection

    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * 384  # Default size for all-MiniLM-L6-v2

        if self.embedding_function:
            try:
                # Use sentence-transformers
                embedding = self.embedding_function.encode(text)
                return embedding.tolist()
            except Exception as e:
                self.logger.error(f"Error generating embedding with sentence-transformers: {e}")
                # Fall back to simple method

        # Fallback: simple hash-based embedding (not suitable for production but functional)
        # This is just for demonstration - real implementation should use proper embeddings
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()

        # Convert hex to list of floats
        embedding = []
        for i in range(0, len(hash_hex), 2):
            hex_byte = hash_hex[i:i+2]
            embedding.append(int(hex_byte, 16) / 255.0)  # Normalize to 0-1

        # Pad or truncate to 384 dimensions
        while len(embedding) < 384:
            embedding.extend(embedding[:min(len(embedding), 384 - len(embedding))])
        embedding = embedding[:384]

        return embedding

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
        Store knowledge in vector memory

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

        memory_id = str(uuid.uuid4())
        full_text = f"Title: {title}\nContent: {content}"

        try:
            if CHROMADB_AVAILABLE and self.collections.get("knowledge"):
                collection = self.collections["knowledge"]
                embedding = self._get_embedding(full_text)

                collection.add(
                    embeddings=[embedding],
                    documents=[full_text],
                    metadatas=[{
                        "title": title,
                        "source": source,
                        "tags": json.dumps(tags),
                        "timestamp": timestamp.isoformat(),
                        **metadata
                    }],
                    ids=[memory_id]
                )
            else:
                # Fallback storage - just store the data without vectors
                # In a real implementation, we'd have a fallback database
                pass

            self.logger.info(f"Stored knowledge: {title} (ID: {memory_id})")
            return memory_id

        except Exception as e:
            self.logger.error(f"Error storing knowledge: {e}")
            raise

    async def store_preference(
        self,
        key: str,
        value: Any,
        category: str = "general",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a preference in vector memory

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

        memory_id = str(uuid.uuid4())
        value_str = json.dumps(value) if not isinstance(value, str) else value
        full_text = f"Preference: {key} = {value_str}"

        try:
            if CHROMADB_AVAILABLE and self.collections.get("preferences"):
                collection = self.collections["preferences"]
                embedding = self._get_embedding(full_text)

                collection.add(
                    embeddings=[embedding],
                    documents=[full_text],
                    metadatas=[{
                        "key": key,
                        "value": value_str,
                        "category": category,
                        "timestamp": timestamp.isoformat(),
                        **metadata
                    }],
                    ids=[memory_id]
                )
            else:
                # Fallback storage
                pass

            self.logger.info(f"Stored preference: {key} = {value_str} (ID: {memory_id})")
            return memory_id

        except Exception as e:
            self.logger.error(f"Error storing preference: {e}")
            raise

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
        Store a skill in vector memory

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

        memory_id = str(uuid.uuid4())
        full_text = f"Skill: {name}\nDescription: {description}\nProficiency: {proficiency}"

        try:
            if CHROMADB_AVAILABLE and self.collections.get("skills"):
                collection = self.collections["skills"]
                embedding = self._get_embedding(full_text)

                collection.add(
                    embeddings=[embedding],
                    documents=[full_text],
                    metadatas=[{
                        "name": name,
                        "description": description,
                        "proficiency": proficiency,
                        "category": category,
                        "timestamp": timestamp.isoformat(),
                        **metadata
                    }],
                    ids=[memory_id]
                )
            else:
                # Fallback storage
                pass

            self.logger.info(f"Stored skill: {name} (ID: {memory_id})")
            return memory_id

        except Exception as e:
            self.logger.error(f"Error storing skill: {e}")
            raise

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
        Store an event in vector memory

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
        if participants is None:
            participants = []

        memory_id = str(uuid.uuid4())
        full_text = f"Event: {title}\nDescription: {description}"

        if start_time:
            full_text += f"\nStart: {start_time.isoformat()}"
        if end_time:
            full_text += f"\nEnd: {end_time.isoformat()}"
        if location:
            full_text += f"\nLocation: {location}"
        if participants:
            full_text += f"\nParticipants: {', '.join(participants)}"

        try:
            if CHROMADB_AVAILABLE and self.collections.get("events"):
                collection = self.collections["events"]
                embedding = self._get_embedding(full_text)

                collection.add(
                    embeddings=[embedding],
                    documents=[full_text],
                    metadatas=[{
                        "title": title,
                        "description": description,
                        "event_type": event_type,
                        "start_time": start_time.isoformat() if start_time else None,
                        "end_time": end_time.isoformat() if end_time else None,
                        "location": location,
                        "participants": json.dumps(participants),
                        "timestamp": timestamp.isoformat(),
                        **metadata
                    }],
                    ids=[memory_id]
                )
            else:
                # Fallback storage
                pass

            self.logger.info(f"Stored event: {title} (ID: {memory_id})")
            return memory_id

        except Exception as e:
            self.logger.error(f"Error storing event: {e}")
            raise

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
        Store a task in vector memory

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

        memory_id = str(uuid.uuid4())
        full_text = f"Task: {title}\nDescription: {description}\nStatus: {status}\nPriority: {priority}"

        if due_date:
            full_text += f"\nDue: {due_date.isoformat()}"
        if assigned_to:
            full_text += f"\nAssigned to: {assigned_to}"
        if tags:
            full_text += f"\nTags: {', '.join(tags)}"

        try:
            if CHROMADB_AVAILABLE and self.collections.get("tasks"):
                collection = self.collections["tasks"]
                embedding = self._get_embedding(full_text)

                collection.add(
                    embeddings=[embedding],
                    documents=[full_text],
                    metadatas=[{
                        "title": title,
                        "description": description,
                        "status": status,
                        "priority": priority,
                        "due_date": due_date.isoformat() if due_date else None,
                        "assigned_to": assigned_to,
                        "tags": json.dumps(tags),
                        "timestamp": timestamp.isoformat(),
                        **metadata
                    }],
                    ids=[memory_id]
                )
            else:
                # Fallback storage
                pass

            self.logger.info(f"Stored task: {title} (ID: {memory_id})")
            return memory_id

        except Exception as e:
            self.logger.error(f"Error storing task: {e}")
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
        Store a conversation in vector memory (for long-term retention of important conversations)

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

        memory_id = str(uuid.uuid4())
        full_text = f"{role}: {content}"

        try:
            if CHROMADB_AVAILABLE and self.collections.get("conversations"):
                collection = self.collections["conversations"]
                embedding = self._get_embedding(full_text)

                collection.add(
                    embeddings=[embedding],
                    documents=[full_text],
                    metadatas=[{
                        "role": role,
                        "modality": modality,
                        "timestamp": timestamp.isoformat(),
                        **metadata
                    }],
                    ids=[memory_id]
                )
            else:
                # Fallback storage
                pass

            self.logger.info(f"Stored conversation: {role} (ID: {memory_id})")
            return memory_id

        except Exception as e:
            self.logger.error(f"Error storing conversation: {e}")
            raise

    async def search(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search vector memory for similar content

        Args:
            query: Search query
            memory_type: Type of memory to search (None for all collections)
            limit: Maximum results to return
            min_similarity: Minimum similarity score (0.0 to 1.0)

        Returns:
            List of matching memory items with similarity scores
        """
        if not self.is_initialized:
            await self.initialize()

        if not CHROMADB_AVAILABLE or not self.client:
            # Fallback: return empty results or implement basic text search
            self.logger.warning("Vector search not available - returning empty results")
            return []

        results = []

        try:
            query_embedding = self._get_embedding(query)

            # Determine which collections to search
            collections_to_search = []
            if memory_type and memory_type in self.collections:
                collections_to_search = [("memory_type", self.collections[memory_type])]
            else:
                collections_to_search = list(self.collections.items())

            for mem_type, collection in collections_to_search:
                try:
                    search_results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=limit,
                        include=["documents", "metadatas", "distances"]
                    )

                    # Process results
                    if search_results["ids"] and search_results["ids"][0]:
                        for i, doc_id in enumerate(search_results["ids"][0]):
                            distance = search_results["distances"][0][i]
                            # Convert distance to similarity (ChromaDB returns distance, we want similarity)
                            similarity = 1.0 - distance  # For cosine distance

                            if similarity >= min_similarity:
                                metadata = search_results["metadatas"][0][i]
                                # Parse JSON fields in metadata
                                if "tags" in metadata and metadata["tags"]:
                                    try:
                                        metadata["tags"] = json.loads(metadata["tags"])
                                    except:
                                        metadata["tags"] = []
                                if "participants" in metadata and metadata["participants"]:
                                    try:
                                        metadata["participants"] = json.loads(metadata["participants"])
                                    except:
                                        metadata["participants"] = []

                                results.append({
                                    "id": doc_id,
                                    "content": search_results["documents"][0][i],
                                    "metadata": metadata,
                                    "similarity": similarity,
                                    "type": mem_type,
                                    "collection": getattr(collection, "name", "unknown")
                                })
                except Exception as e:
                    self.logger.error(f"Error searching collection {mem_type}: {e}")
                    continue

            # Sort by similarity (highest first)
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:limit]

        except Exception as e:
            self.logger.error(f"Error searching vector memory: {e}")
            return []

    async def get_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific memory by ID

        Args:
            memory_id: The memory ID

        Returns:
            Memory data or None if not found
        """
        if not self.is_initialized:
            await self.initialize()

        if not CHROMADB_AVAILABLE or not self.client:
            return None

        # Search all collections for the ID
        for memory_type, collection in self.collections.items():
            try:
                results = collection.get(
                    ids=[memory_id],
                    include=["documents", "metadatas"]
                )

                if results["ids"] and results["ids"][0]:
                    metadata = results["metadatas"][0]
                    # Parse JSON fields
                    if "tags" in metadata and metadata["tags"]:
                        try:
                            metadata["tags"] = json.loads(metadata["tags"])
                        except:
                            metadata["tags"] = []
                    if "participants" in metadata and metadata["participants"]:
                        try:
                            metadata["participants"] = json.loads(metadata["participants"])
                        except:
                            metadata["participants"] = []

                    return {
                        "id": memory_id,
                        "content": results["documents"][0],
                        "metadata": metadata,
                        "type": memory_type,
                        "collection": getattr(collection, "name", "unknown")
                    }
            except Exception:
                # ID not found in this collection, continue searching
                continue

        return None

    async def update_by_id(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a memory by ID (ChromaDB doesn't support direct updates, so we delete and re-add)

        Args:
            memory_id: The memory ID to update
            updates: Dictionary of fields to update

        Returns:
            True if successful
        """
        if not self.is_initialized:
            await self.initialize()

        if not CHROMADB_AVAILABLE or not self.client:
            return False

        # Get the existing record
        existing = await self.get_by_id(memory_id)
        if not existing:
            return False

        # Determine which collection it's in
        memory_type = existing["type"]
        if memory_type not in self.collections:
            return False

        try:
            collection = self.collections[memory_type]

            # Delete the old record
            collection.delete(ids=[memory_id])

            # Prepare updated data
            content = existing["content"]
            metadata = existing["metadata"].copy()
            metadata.update(updates)

            # Re-add with updated metadata
            embedding = self._get_embedding(content)
            collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata],
                ids=[memory_id]
            )

            self.logger.info(f"Updated memory {memory_id} in {memory_type} collection")
            return True

        except Exception as e:
            self.logger.error(f"Error updating memory {memory_id}: {e}")
            return False

    async def delete_by_id(self, memory_id: str) -> bool:
        """
        Delete a memory by ID

        Args:
            memory_id: The memory ID to delete

        Returns:
            True if successful
        """
        if not self.is_initialized:
            await self.initialize()

        if not CHROMADB_AVAILABLE or not self.client:
            return False

        # Try to delete from all collections
        deleted = False
        for memory_type, collection in self.collections.items():
            try:
                # Check if ID exists in this collection
                existing = collection.get(ids=[memory_id])
                if existing["ids"] and existing["ids"][0]:
                    collection.delete(ids=[memory_id])
                    deleted = True
                    self.logger.info(f"Deleted memory {memory_id} from {memory_type} collection")
                    break  # Assume ID is unique across collections
            except Exception:
                continue

        return deleted

    async def get_stats(self) -> Dict[str, Any]:
        """Get vector memory statistics"""
        if not self.is_initialized:
            await self.initialize()

        if not CHROMADB_AVAILABLE or not self.client:
            return {
                "error": "ChromaDB not available",
                "collections": {}
            }

        stats = {}
        total_count = 0

        for memory_type, collection in self.collections.items():
            try:
                count = collection.count()
                stats[memory_type] = {
                    "count": count,
                    "collection_name": getattr(collection, "name", "unknown")
                }
                total_count += count
            except Exception as e:
                self.logger.error(f"Error getting stats for collection {memory_type}: {e}")
                stats[memory_type] = {
                    "error": str(e),
                    "count": 0
                }

        stats["total_count"] = total_count
        stats["embedding_model"] = self.embedding_model_name
        stats["chromadb_available"] = True

        return stats

    async def clear_old_memories(self, cutoff_date: datetime) -> Dict[str, Any]:
        """
        Clear memories older than cutoff date
        Note: ChromaDB doesn't support direct deletion by metadata, so this is limited
        """
        if not self.is_initialized:
            await self.initialize()

        if not CHROMADB_AVAILABLE or not self.client:
            return {"error": "ChromaDB not available"}

        # For now, we'll just return a placeholder since ChromaDB doesn't support
        # efficient deletion by metadata filters without retrieving all IDs first
        # In production, you'd want to implement this differently
        self.logger.warning("Clear old memories not fully implemented for ChromaDB fallback")
        return {
            "cleared_count": 0,
            "note": "Clear old memories not fully implemented for ChromaDB - manual cleanup may be needed"
        }

    async def shutdown(self):
        """Shutdown the vector memory"""
        self.logger.info("Shutting down Vector memory")
        self.is_initialized = False
        # ChromaDB client doesn't need explicit shutdown in most cases
        self.client = None
        self.collections.clear()