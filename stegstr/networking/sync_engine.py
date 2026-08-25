"""
Nostr Synchronization & Event Deduplication Engine

Synchronizes missed events from relays and maintains deduplicated event cache.
"""

import asyncio
import json
from typing import Dict, Any, List
from stegstr.storage.db import DatabaseManager
from stegstr.nostr.events import NostrEvent


class SyncEngine:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.seen_event_ids = set()

    def sync_local_event(self, event: NostrEvent, carrier_path: str = None) -> bool:
        """Store decoded steganographic event into local SQLite database."""
        if event.id in self.seen_event_ids:
            return False
        self.seen_event_ids.add(event.id)
        self.db.save_event(event, carrier_path=carrier_path, synced=False)
        return True

    def get_feed(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve local timeline feed."""
        return self.db.get_events(limit=limit)
