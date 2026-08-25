"""
Offline Queue & Auto-Reconnection Synchronization Manager
"""

import asyncio
from typing import Dict, Any, List
from stegstr.storage.db import DatabaseManager
from stegstr.networking.relay_manager import RelayPoolManager


class OfflineQueueManager:
    def __init__(self, db: DatabaseManager, pool: RelayPoolManager):
        self.db = db
        self.pool = pool

    async def flush_queue(self) -> Dict[str, Any]:
        """Flush queued offline events to relays upon network restoration."""
        queued = self.db.get_queued_events()
        if not queued:
            return {"flushed": 0, "status": "EMPTY"}

        flushed_count = 0
        failed_count = 0

        for item in queued:
            event_dict = json.loads(item["event_json"])
            res = await self.pool.publish_event_to_relays(event_dict)
            if res.get("published", 0) > 0:
                self.db.remove_from_offline_queue(item["id"])
                flushed_count += 1
            else:
                failed_count += 1

        return {
            "flushed": flushed_count,
            "failed": failed_count,
            "total": len(queued)
        }
