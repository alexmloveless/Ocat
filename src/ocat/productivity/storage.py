"""
Storage abstraction for productivity entities.

Provides a clean interface for storing and retrieving productivity entities
(tasks, events, reminders, memories) using the existing Ocat vector store.
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Type, cast

from .models import (
    ProductivityEntity,
    Task,
    Event,
    Reminder,
    Memory,
    ListItem,
    TimelogEntry,
    EntityType,
    EntityStatus,
    create_entity,
)
from ..vector_store import ConversationVectorStore
from ..config import Config
from ..exceptions import VectorStoreError


class ProductivityStorage:
    """
    Storage abstraction for productivity entities.

    Wraps the existing ConversationVectorStore to provide specialized
    methods for productivity entity management with pseudo IDs,
    search, and filtering capabilities.
    """

    def __init__(self, vector_store: ConversationVectorStore):
        """
        Initialize productivity storage.

        Parameters
        ----------
        vector_store : ConversationVectorStore
            The underlying vector store instance
        """
        self.vector_store = vector_store
        self._lock = threading.RLock()  # Thread-safe operations

        # Pseudo ID counters for each entity type
        self._id_counters: Dict[EntityType, int] = {
            EntityType.TASK: 0,
            EntityType.EVENT: 0,
            EntityType.REMINDER: 0,
            EntityType.MEMORY: 0,
            EntityType.LIST_ITEM: 0,
            EntityType.TIMELOG: 0,
        }

        # Cache for pseudo ID to exchange ID mapping
        self._pseudo_id_map: Dict[str, str] = {}

        # Initialize counters from existing entities
        self._initialize_counters()

    def _initialize_counters(self) -> None:
        """Initialize pseudo ID counters from existing entities."""
        try:
            # Query all productivity entities from vector store
            all_entities = self._get_all_productivity_entities()

            # Track highest pseudo ID for each entity type
            for entity in all_entities:
                if entity.pseudo_id:
                    # Extract number from pseudo ID (e.g., "task123" -> 123)
                    try:
                        num_part = "".join(filter(str.isdigit, entity.pseudo_id))
                        if num_part:
                            num = int(num_part)
                            self._id_counters[entity.entity_type] = max(
                                self._id_counters[entity.entity_type], num
                            )
                            # Cache pseudo ID mapping
                            exchange_id = self._find_exchange_id_for_entity(entity)
                            if exchange_id:
                                self._pseudo_id_map[entity.pseudo_id] = exchange_id
                    except ValueError:
                        continue
        except Exception as e:
            # If initialization fails, start with counters at 0
            pass

    def _get_all_productivity_entities(self) -> List[ProductivityEntity]:
        """Get all productivity entities from vector store."""
        entities = []

        # Search vector store for productivity entities
        # Use a broad search query to find all entity types
        try:
            results = self.vector_store.collection.get()

            docs = results.get("documents", []) or []
            metadatas = results.get("metadatas", []) or []

            for i, doc in enumerate(docs):
                if i < len(metadatas) and metadatas[i] is not None:
                    metadata = cast(Dict[str, Any], metadatas[i])
                    if "entity_type" in metadata:
                        try:
                            entity = self._metadata_to_entity(metadata, doc)
                            if entity:
                                entities.append(entity)
                        except Exception:
                            continue
        except Exception:
            # If ChromaDB query fails, fall back to metadata search
            pass

        return entities

    def _find_exchange_id_for_entity(self, entity: ProductivityEntity) -> Optional[str]:
        """Find the exchange ID for a given entity."""
        # Search through ChromaDB first
        try:
            results = self.vector_store.collection.get()
            docs = results.get("documents", []) or []
            metadatas = results.get("metadatas", []) or []
            ids = results.get("ids", []) or []

            for i, metadata in enumerate(metadatas):
                if metadata is not None:
                    metadata_dict = cast(Dict[str, Any], metadata)
                    if metadata_dict.get("entity_pseudo_id") == entity.pseudo_id:
                        return ids[i] if i < len(ids) else None
        except Exception:
            pass
        return None

    def _generate_pseudo_id(self, entity_type: EntityType) -> str:
        """Generate a new pseudo ID for an entity."""
        with self._lock:
            self._id_counters[entity_type] += 1
            return f"{entity_type.value}{self._id_counters[entity_type]:03d}"

    def _metadata_to_entity(
        self, metadata: Dict[str, Any], content: str
    ) -> Optional[ProductivityEntity]:
        """Convert vector store metadata back to entity."""
        try:
            entity_type = EntityType(metadata.get("entity_type"))

            # Extract entity data from metadata
            entity_data = {
                "content": metadata.get(
                    "entity_content",
                    (
                        content.split("Assistant: ")[-1]
                        if "Assistant: " in content
                        else content
                    ),
                ),
                "pseudo_id": metadata.get("entity_pseudo_id"),
                "status": (
                    EntityStatus(metadata["entity_status"])
                    if metadata.get("entity_status")
                    else None
                ),
                "created_at": (
                    datetime.fromisoformat(metadata["entity_created_at"])
                    if "entity_created_at" in metadata
                    else datetime.now()
                ),
                "updated_at": (
                    datetime.fromisoformat(metadata["entity_updated_at"])
                    if "entity_updated_at" in metadata
                    else None
                ),
                "metadata": json.loads(metadata.get("entity_metadata", "{}")),
            }

            # Add type-specific fields
            if entity_type == EntityType.TASK:
                entity_data.update(
                    {
                        "due_date": (
                            datetime.fromisoformat(metadata["task_due_date"])
                            if metadata.get("task_due_date")
                            else None
                        ),
                        "category": metadata.get("task_category"),
                        "tags": json.loads(metadata.get("task_tags", "[]")),
                        "priority": metadata.get("task_priority"),
                    }
                )
            elif entity_type == EntityType.EVENT:
                entity_data.update(
                    {
                        "start_datetime": datetime.fromisoformat(
                            metadata["event_start_datetime"]
                        ),
                        "end_datetime": (
                            datetime.fromisoformat(metadata["event_end_datetime"])
                            if metadata.get("event_end_datetime")
                            else None
                        ),
                        "all_day": str(metadata.get("event_all_day", "False")).lower()
                        == "true",
                        "participants": json.loads(
                            metadata.get("event_participants", "[]")
                        ),
                        "location": metadata.get("event_location"),
                    }
                )
            elif entity_type == EntityType.REMINDER:
                entity_data.update(
                    {
                        "trigger_datetime": datetime.fromisoformat(
                            metadata["reminder_trigger_datetime"]
                        ),
                        "category": metadata.get("reminder_category"),
                        "recurring": str(
                            metadata.get("reminder_recurring", "False")
                        ).lower()
                        == "true",
                    }
                )
            elif entity_type == EntityType.MEMORY:
                entity_data.update(
                    {
                        "category": metadata.get("memory_category"),
                        "tags": json.loads(metadata.get("memory_tags", "[]")),
                    }
                )
            elif entity_type == EntityType.LIST_ITEM:
                entity_data.update(
                    {
                        "list_name": metadata.get("list_item_list_name"),
                        "category": metadata.get("list_item_category"),
                        "tags": json.loads(metadata.get("list_item_tags", "[]")),
                    }
                )
            elif entity_type == EntityType.TIMELOG:
                from datetime import date
                entity_data.update(
                    {
                        "day": datetime.fromisoformat(metadata["timelog_day"]).date() if metadata.get("timelog_day") else date.today(),
                        "project": metadata.get("timelog_project"),
                        "hours": float(metadata.get("timelog_hours", 0)),
                        "notes": metadata.get("timelog_notes"),
                    }
                )
            return create_entity(entity_type, **entity_data)

        except Exception as e:
            return None

    def _entity_to_metadata(self, entity: ProductivityEntity) -> Dict[str, Any]:
        """Convert entity to vector store metadata format."""
        metadata = {
            "entity_type": (
                entity.entity_type.value
                if hasattr(entity.entity_type, "value")
                else entity.entity_type
            ),
            "entity_content": entity.content,
            "entity_pseudo_id": entity.pseudo_id,
            "entity_status": (
                entity.status.value
                if entity.status and hasattr(entity.status, "value")
                else (entity.status if entity.status else None)
            ),
            "entity_created_at": entity.created_at.isoformat(),
            "entity_updated_at": (
                entity.updated_at.isoformat() if entity.updated_at else None
            ),
            "entity_metadata": json.dumps(entity.metadata),
        }

        # Add type-specific metadata
        if isinstance(entity, Task):
            metadata.update(
                {
                    "task_due_date": (
                        entity.due_date.isoformat() if entity.due_date else None
                    ),
                    "task_category": entity.category,
                    "task_tags": json.dumps(entity.tags),
                    "task_priority": entity.priority,
                }
            )
        elif isinstance(entity, Event):
            metadata.update(
                {
                    "event_start_datetime": entity.start_datetime.isoformat(),
                    "event_end_datetime": (
                        entity.end_datetime.isoformat() if entity.end_datetime else None
                    ),
                    "event_all_day": str(entity.all_day),
                    "event_participants": json.dumps(entity.participants),
                    "event_location": entity.location,
                }
            )
        elif isinstance(entity, Reminder):
            metadata.update(
                {
                    "reminder_trigger_datetime": entity.trigger_datetime.isoformat(),
                    "reminder_category": entity.category,
                    "reminder_recurring": str(entity.recurring),
                }
            )
        elif isinstance(entity, Memory):
            metadata.update(
                {
                    "memory_category": entity.category,
                    "memory_tags": json.dumps(entity.tags),
                }
            )
        elif isinstance(entity, ListItem):
            metadata.update(
                {
                    "list_item_list_name": entity.list_name,
                    "list_item_category": entity.category,
                    "list_item_tags": json.dumps(entity.tags),
                }
            )
        elif isinstance(entity, TimelogEntry):
            metadata.update(
                {
                    "timelog_day": entity.day.isoformat(),
                    "timelog_project": entity.project,
                    "timelog_hours": str(entity.hours),
                    "timelog_notes": entity.notes,
                }
            )

        return metadata

    def create_entity(self, entity: ProductivityEntity) -> str:
        """
        Create a new productivity entity.

        Parameters
        ----------
        entity : ProductivityEntity
            The entity to store

        Returns
        -------
        str
            The pseudo ID of the created entity

        Raises
        ------
        VectorStoreError
            If storage fails
        """
        with self._lock:
            try:
                # Generate pseudo ID if not provided
                if not entity.pseudo_id:
                    entity_type = (
                        EntityType(entity.entity_type)
                        if isinstance(entity.entity_type, str)
                        else entity.entity_type
                    )
                    entity.pseudo_id = self._generate_pseudo_id(entity_type)

                # Set timestamps
                if not entity.created_at:
                    entity.created_at = datetime.now()
                entity.updated_at = datetime.now()

                # Convert to metadata format
                metadata = self._entity_to_metadata(entity)

                # Create a user prompt that represents the entity creation
                entity_type_str = (
                    entity.entity_type.value
                    if hasattr(entity.entity_type, "value")
                    else entity.entity_type
                )
                user_prompt = f"Create {entity_type_str}: {entity.content}"
                assistant_response = (
                    f"Created {entity_type_str} {entity.pseudo_id}: {entity.content}"
                )

                # Store in vector store
                exchange_id = self.vector_store.add_exchange(
                    user_prompt=user_prompt,
                    assistant_response=assistant_response,
                    thread_id="productivity_system",
                    session_id="productivity_session",
                )

                # Update ChromaDB metadata with entity information
                try:
                    self.vector_store.collection.update(
                        ids=[exchange_id],
                        metadatas=[
                            {
                                **metadata,
                                **{
                                    "exchange_id": exchange_id,
                                    "thread_id": "productivity_system",
                                    "session_id": "productivity_session",
                                    "timestamp": str(time.time()),
                                },
                            }
                        ],
                    )
                except Exception as e:
                    # If ChromaDB update fails, continue - the basic exchange is still stored
                    pass

                # Cache pseudo ID mapping
                self._pseudo_id_map[entity.pseudo_id] = exchange_id

                return entity.pseudo_id

            except Exception as e:
                raise VectorStoreError(f"Failed to create entity: {e}")

    def get_entity_by_pseudo_id(self, pseudo_id: str) -> Optional[ProductivityEntity]:
        """
        Get an entity by its pseudo ID.

        Parameters
        ----------
        pseudo_id : str
            The pseudo ID to search for

        Returns
        -------
        Optional[ProductivityEntity]
            The entity if found, None otherwise
        """
        try:
            # Search ChromaDB by pseudo ID
            try:
                results = self.vector_store.collection.get()

                docs = results.get("documents", []) or []
                metadatas = results.get("metadatas", []) or []
                ids = results.get("ids", []) or []

                for i, metadata in enumerate(metadatas):
                    if metadata is not None:
                        metadata_dict = cast(Dict[str, Any], metadata)
                        if metadata_dict.get("entity_pseudo_id") == pseudo_id:
                            doc = docs[i] if i < len(docs) else ""
                            entity = self._metadata_to_entity(metadata_dict, doc)

                            # Update cache
                            if entity and i < len(ids):
                                self._pseudo_id_map[pseudo_id] = ids[i]

                            return entity
            except Exception:
                pass

            return None

        except Exception as e:
            return None

    def update_entity(self, pseudo_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an entity by pseudo ID.

        Parameters
        ----------
        pseudo_id : str
            The pseudo ID of the entity to update
        updates : Dict[str, Any]
            Fields to update

        Returns
        -------
        bool
            True if update succeeded, False otherwise
        """
        with self._lock:
            try:
                # Get existing entity
                entity = self.get_entity_by_pseudo_id(pseudo_id)
                if not entity:
                    return False

                # Apply updates
                entity_dict = entity.model_dump()
                old_status = entity_dict.get("status")
                entity_dict.update(updates)
                entity_dict["updated_at"] = datetime.now()
                new_status = entity_dict.get("status")

                # Create updated entity
                # Remove entity_type from dict since it's passed as first arg
                entity_dict_clean = entity_dict.copy()
                entity_dict_clean.pop("entity_type", None)
                updated_entity = create_entity(entity.entity_type, **entity_dict_clean)
                updated_entity.pseudo_id = pseudo_id  # Preserve pseudo ID

                # Debug: Check if status actually changed
                final_status = (
                    updated_entity.status.value if updated_entity.status else None
                )

                # Get exchange ID - need to search through vector store
                exchange_id = self._pseudo_id_map.get(pseudo_id)
                if not exchange_id:
                    # Search ChromaDB for the entity
                    try:
                        results = self.vector_store.collection.get()
                        docs = results.get("documents", []) or []
                        metadatas = results.get("metadatas", []) or []
                        ids = results.get("ids", []) or []

                        for i, metadata in enumerate(metadatas):
                            if metadata is not None:
                                metadata_dict = cast(Dict[str, Any], metadata)
                                if metadata_dict.get("entity_pseudo_id") == pseudo_id:
                                    exchange_id = ids[i] if i < len(ids) else None
                                    if exchange_id:
                                        self._pseudo_id_map[pseudo_id] = exchange_id
                                    break
                    except Exception:
                        pass

                    if not exchange_id:
                        return False

                # Update metadata in ChromaDB
                metadata = self._entity_to_metadata(updated_entity)

                try:
                    self.vector_store.collection.update(
                        ids=[exchange_id],
                        metadatas=[
                            {
                                **metadata,
                                **{
                                    "exchange_id": exchange_id,
                                    "thread_id": "productivity_system",
                                    "session_id": "productivity_session",
                                    "timestamp": str(time.time()),
                                },
                            }
                        ],
                    )
                    return True
                except Exception as e:
                    print(f"ChromaDB update failed: {e}")
                    return False

            except Exception as e:
                print(f"Entity update failed: {e}")
                return False

    def delete_entity(self, pseudo_id: str) -> bool:
        """
        Soft delete an entity by setting status to DELETED.

        Parameters
        ----------
        pseudo_id : str
            The pseudo ID of the entity to delete

        Returns
        -------
        bool
            True if deletion succeeded, False otherwise
        """
        return self.update_entity(pseudo_id, {"status": EntityStatus.DELETED})

    def search_entities(
        self,
        query: str = "",
        entity_types: Optional[List[EntityType]] = None,
        status: Optional[EntityStatus] = None,
        limit: int = 10,
    ) -> List[ProductivityEntity]:
        """
        Search for entities by text and filters.

        Parameters
        ----------
        query : str
            Text query for similarity search
        entity_types : Optional[List[EntityType]]
            Filter by entity types
        status : Optional[EntityStatus]
            Filter by status
        limit : int
            Maximum number of results

        Returns
        -------
        List[ProductivityEntity]
            List of matching entities
        """
        try:
            entities = []

            try:
                if query:
                    # Use vector similarity search
                    results = self.vector_store.collection.query(
                        query_texts=[query],
                        n_results=limit * 2,  # Get more to allow filtering
                    )

                    docs_list = results.get("documents", [[]])
                    metadatas_list = results.get("metadatas", [[]])

                    if docs_list and metadatas_list:
                        docs = docs_list[0]
                        metadatas = metadatas_list[0]

                        for i, doc in enumerate(docs):
                            if i < len(metadatas):
                                metadata = cast(Dict[str, Any], metadatas[i])
                                if "entity_type" in metadata:
                                    # Filter by entity type
                                    if entity_types:
                                        entity_type_str = metadata.get("entity_type")
                                        if entity_type_str not in [
                                            et.value for et in entity_types
                                        ]:
                                            continue

                                    entity = self._metadata_to_entity(metadata, doc)

                                    if entity:
                                        # When status param is None, include all entities
                                        # When status param is set, only include matching entities
                                        include_entity = (status is None) or (
                                            entity.status == status
                                        )
                                        if include_entity:
                                            entities.append(entity)

                                        if len(entities) >= limit:
                                            break
                else:
                    # Get all entities and filter
                    all_results = self.vector_store.collection.get()

                    docs = all_results.get("documents", []) or []
                    metadatas = all_results.get("metadatas", []) or []

                    for i, doc in enumerate(docs):
                        if i < len(metadatas) and metadatas[i] is not None:
                            metadata = cast(Dict[str, Any], metadatas[i])
                            if "entity_type" in metadata:
                                # Filter by entity type
                                if entity_types:
                                    entity_type_str = metadata.get("entity_type")
                                    if entity_type_str not in [
                                        et.value for et in entity_types
                                    ]:
                                        continue

                                entity = self._metadata_to_entity(metadata, doc)

                                # Debug: Check what's happening with status filtering
                                if entity:
                                    # When status param is None, include all entities
                                    # When status param is set, only include matching entities
                                    include_entity = (status is None) or (
                                        entity.status == status
                                    )
                                    if include_entity:
                                        entities.append(entity)

                                    if len(entities) >= limit:
                                        break

            except Exception:
                pass

            return entities

        except Exception as e:
            return []

    def get_entities_by_type(
        self,
        entity_type: EntityType,
        status: Optional[EntityStatus] = None,
        limit: int = 50,
    ) -> List[ProductivityEntity]:
        """
        Get all entities of a specific type.

        Parameters
        ----------
        entity_type : EntityType
            The type of entities to retrieve
        status : Optional[EntityStatus]
            Filter by status (None means all statuses)
        limit : int
            Maximum number of results

        Returns
        -------
        List[ProductivityEntity]
            List of entities of the specified type
        """
        return self.search_entities(
            entity_types=[entity_type], status=status, limit=limit
        )
