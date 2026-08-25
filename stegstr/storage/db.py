"""
Stegstr SQLite Database Manager

Handles local persistence for Nostr identities, events, relay states,
offline message queue, and steganography benchmark history.
"""

import json
import sqlite3
from typing import Dict, Any, List, Optional
from pathlib import Path

from stegstr.config import DB_PATH, DEFAULT_RELAYS
from stegstr.nostr.events import NostrEvent
from stegstr.nostr.keys import NostrKeyPair


class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # Identities table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS identities (
                pubkey TEXT PRIMARY KEY,
                privkey TEXT NOT NULL,
                nsec TEXT NOT NULL,
                npub TEXT NOT NULL,
                name TEXT DEFAULT 'Anonymous',
                is_active INTEGER DEFAULT 0,
                created_at INTEGER NOT NULL
            );
            """)

            # Events table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                pubkey TEXT NOT NULL,
                kind INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                content TEXT NOT NULL,
                tags TEXT NOT NULL,
                sig TEXT NOT NULL,
                synced INTEGER DEFAULT 0,
                carrier_path TEXT
            );
            """)

            # Relays table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS relays (
                url TEXT PRIMARY KEY,
                status TEXT DEFAULT 'UNKNOWN',
                latency_ms INTEGER DEFAULT -1,
                last_sync INTEGER DEFAULT 0,
                is_enabled INTEGER DEFAULT 1,
                error_count INTEGER DEFAULT 0
            );
            """)

            # Offline Queue table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS offline_queue (
                id TEXT PRIMARY KEY,
                event_json TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                attempts INTEGER DEFAULT 0
            );
            """)

            # Benchmark table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                codec TEXT NOT NULL,
                recovery_rate REAL NOT NULL,
                psnr REAL NOT NULL,
                ssim REAL NOT NULL,
                details_json TEXT NOT NULL
            );
            """)

            # Populate default relays if table empty
            cursor.execute("SELECT COUNT(*) FROM relays")
            if cursor.fetchone()[0] == 0:
                for relay in DEFAULT_RELAYS:
                    cursor.execute("INSERT OR IGNORE INTO relays (url) VALUES (?)", (relay,))

            conn.commit()

    # Identity Management
    def save_identity(self, keypair: NostrKeyPair, name: str = "Anonymous", is_active: bool = True) -> Dict[str, Any]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if is_active:
                cursor.execute("UPDATE identities SET is_active = 0")
            cursor.execute("""
            INSERT OR REPLACE INTO identities (pubkey, privkey, nsec, npub, name, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, strftime('%s', 'now'))
            """, (keypair.public_key_hex, keypair.private_key_hex, keypair.nsec, keypair.npub, name, 1 if is_active else 0))
            conn.commit()
        return {"pubkey": keypair.public_key_hex, "npub": keypair.npub, "name": name}

    def get_active_identity(self) -> Optional[NostrKeyPair]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT privkey FROM identities WHERE is_active = 1 LIMIT 1")
            row = cursor.fetchone()
            if row:
                return NostrKeyPair(row["privkey"])
            
            # Generate default anonymous keypair if none active
            new_kp = NostrKeyPair.generate_anonymous()
            self.save_identity(new_kp, name="Anonymous Identity", is_active=True)
            return new_kp

    # Event Management
    def save_event(self, event: NostrEvent, carrier_path: Optional[str] = None, synced: bool = False):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO events (id, pubkey, kind, created_at, content, tags, sig, synced, carrier_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.id,
                event.pubkey,
                event.kind,
                event.created_at,
                event.content,
                json.dumps(event.tags),
                event.sig,
                1 if synced else 0,
                carrier_path
            ))
            conn.commit()

    def get_events(self, kind: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if kind is not None:
                cursor.execute("SELECT * FROM events WHERE kind = ? ORDER BY created_at DESC LIMIT ?", (kind, limit))
            else:
                cursor.execute("SELECT * FROM events ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append({
                    "id": r["id"],
                    "pubkey": r["pubkey"],
                    "kind": r["kind"],
                    "created_at": r["created_at"],
                    "content": r["content"],
                    "tags": json.loads(r["tags"]),
                    "sig": r["sig"],
                    "synced": bool(r["synced"]),
                    "carrier_path": r["carrier_path"]
                })
            return results

    # Relay Management
    def get_relays(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM relays ORDER BY url ASC")
            return [dict(r) for r in cursor.fetchall()]

    def update_relay_status(self, url: str, status: str, latency_ms: int = -1):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE relays SET status = ?, latency_ms = ?, last_sync = strftime('%s', 'now') WHERE url = ?
            """, (status, latency_ms, url))
            conn.commit()

    def add_relay(self, url: str):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO relays (url) VALUES (?)", (url,))
            conn.commit()

    def remove_relay(self, url: str):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM relays WHERE url = ?", (url,))
            conn.commit()

    # Offline Queue
    def enqueue_offline_event(self, event: NostrEvent):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO offline_queue (id, event_json, created_at, attempts)
            VALUES (?, ?, strftime('%s', 'now'), 0)
            """, (event.id, json.dumps(event.to_dict())))
            conn.commit()

    def get_queued_events(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM offline_queue ORDER BY created_at ASC")
            return [dict(r) for r in cursor.fetchall()]

    def remove_from_offline_queue(self, event_id: str):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM offline_queue WHERE id = ?", (event_id,))
            conn.commit()
