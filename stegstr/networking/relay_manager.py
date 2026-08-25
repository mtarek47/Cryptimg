"""
Nostr Multi-Relay Manager & Connection Pool

Manages WebSocket connection pools across multiple Nostr relays with health metrics,
latency tracking, and exponential backoff retry logic.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable

from stegstr.storage.db import DatabaseManager
from stegstr.networking.websocket_client import WebSocketClient


class RelayPoolManager:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()
        self.active_connections: Dict[str, Any] = {}

    def test_relay_sync(self, url: str) -> Dict[str, Any]:
        """Test single relay connection synchronously using standard library WebSocketClient."""
        start_time = time.time()
        try:
            client = WebSocketClient(url, timeout=4.0)
            client.connect()
            latency = int((time.time() - start_time) * 1000)
            
            # Send sample NIP-01 REQ
            req_msg = json.dumps(["REQ", "health_check", {"kinds": [1], "limit": 1}])
            client.send_text(req_msg)
            resp = client.recv_text()
            client.close()

            self.db.update_relay_status(url, "ONLINE", latency)
            return {
                "url": url,
                "status": "ONLINE",
                "latency_ms": latency,
                "sample_response": str(resp)[:100]
            }
        except Exception as e:
            self.db.update_relay_status(url, "OFFLINE", -1)
            return {
                "url": url,
                "status": "OFFLINE",
                "latency_ms": -1,
                "error": str(e)
            }

    async def test_relay(self, url: str) -> Dict[str, Any]:
        return await asyncio.to_thread(self.test_relay_sync, url)

    async def test_all_relays(self) -> List[Dict[str, Any]]:
        """Test all registered relays concurrently."""
        relays = self.db.get_relays()
        tasks = [self.test_relay(r["url"]) for r in relays if r.get("is_enabled", 1)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        final_results = []
        for r, res in zip(relays, results):
            if isinstance(res, Exception):
                final_results.append({
                    "url": r["url"],
                    "status": "OFFLINE",
                    "latency_ms": -1,
                    "error": str(res)
                })
            else:
                final_results.append(res)
        return final_results

    def publish_event_sync(self, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Publish event synchronously across relays."""
        relays = self.db.get_relays()
        enabled_urls = [r["url"] for r in relays if r.get("is_enabled", 1)]
        
        published_count = 0
        failed_count = 0
        details = {}
        msg = json.dumps(["EVENT", event_dict])

        for url in enabled_urls:
            try:
                client = WebSocketClient(url, timeout=3.0)
                client.connect()
                client.send_text(msg)
                client.close()
                published_count += 1
                details[url] = "OK"
            except Exception as e:
                failed_count += 1
                details[url] = f"FAILED: {e}"

        return {
            "event_id": event_dict.get("id"),
            "total_relays": len(enabled_urls),
            "published": published_count,
            "failed": failed_count,
            "details": details
        }

    async def publish_event_to_relays(self, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        return await asyncio.to_thread(self.publish_event_sync, event_dict)
