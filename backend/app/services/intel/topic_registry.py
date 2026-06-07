"""Phase 13: Topic Registry for mapping aliases to canonical topics."""

import logging
from typing import List, Optional, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.intel import TopicRegistry
from uuid import UUID

logger = logging.getLogger(__name__)


class TopicRegistryService:
    """Service to normalize topics against the Topic Registry.
    
    Uses a per-call in-memory cache to avoid repeated full-table scans
    within the same worker batch. The cache is workspace-scoped and
    invalidated naturally at the end of each method call boundary.
    """

    # In-memory workspace-scoped cache: {workspace_id: {raw_topic_lower: canonical}}
    _cache: Dict[UUID, Dict[str, str]] = {}

    @classmethod
    def clear_cache(cls, workspace_id: Optional[UUID] = None):
        """Clear the topic cache. Call between worker batches or after writes."""
        if workspace_id:
            cls._cache.pop(workspace_id, None)
        else:
            cls._cache.clear()

    @staticmethod
    async def get_or_create_canonical_topic(
        db: AsyncSession,
        workspace_id: UUID,
        raw_topic: str,
        category: Optional[str] = None
    ) -> str:
        """
        Normalize a raw topic string into a canonical topic.
        If it matches an alias, return the canonical topic.
        If it's new, create a new canonical registry entry.
        Uses a per-workspace in-memory cache to avoid repeated DB scans.
        """
        raw_topic_lower = raw_topic.strip().lower()
        if not raw_topic_lower:
            return "unknown"

        # Check cache first
        ws_cache = TopicRegistryService._cache.get(workspace_id)
        if ws_cache and raw_topic_lower in ws_cache:
            return ws_cache[raw_topic_lower]

        # Load registries from DB (once per workspace per cache miss)
        if ws_cache is None:
            stmt = select(TopicRegistry).where(TopicRegistry.workspace_id == workspace_id)
            result = await db.execute(stmt)
            registries = result.scalars().all()

            # Build cache from loaded data
            ws_cache = {}
            for registry in registries:
                ws_cache[registry.canonical_topic] = registry.canonical_topic
                ws_cache[registry.display_name.lower()] = registry.canonical_topic
                for alias in registry.aliases:
                    ws_cache[alias.lower()] = registry.canonical_topic

            TopicRegistryService._cache[workspace_id] = ws_cache

            # Re-check after cache build
            if raw_topic_lower in ws_cache:
                return ws_cache[raw_topic_lower]
        else:
            # Cache exists but topic not in it — check DB for this specific topic
            # (may have been created by concurrent worker)
            stmt = select(TopicRegistry).where(TopicRegistry.workspace_id == workspace_id)
            result = await db.execute(stmt)
            registries = result.scalars().all()

            for registry in registries:
                if registry.canonical_topic == raw_topic_lower:
                    ws_cache[raw_topic_lower] = registry.canonical_topic
                    return registry.canonical_topic
                if registry.display_name.lower() == raw_topic_lower:
                    ws_cache[raw_topic_lower] = registry.canonical_topic
                    return registry.canonical_topic
                for alias in registry.aliases:
                    if alias.lower() == raw_topic_lower:
                        ws_cache[raw_topic_lower] = registry.canonical_topic
                        return registry.canonical_topic

        # Not found -> create new canonical topic
        canonical = raw_topic_lower.replace(" ", "_")
        new_registry = TopicRegistry(
            workspace_id=workspace_id,
            canonical_topic=canonical,
            display_name=raw_topic.strip().title(),
            aliases=[raw_topic_lower],
            category=category
        )
        db.add(new_registry)
        await db.flush()

        # Update cache
        ws_cache[raw_topic_lower] = canonical
        ws_cache[canonical] = canonical
        TopicRegistryService._cache[workspace_id] = ws_cache

        return canonical

    @staticmethod
    async def normalize_topics(
        db: AsyncSession,
        workspace_id: UUID,
        topics: List[str]
    ) -> List[str]:
        """Normalize a list of topics."""
        normalized = []
        for t in topics:
            canon = await TopicRegistryService.get_or_create_canonical_topic(db, workspace_id, t)
            normalized.append(canon)
        return list(set(normalized))
