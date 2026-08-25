# Nostr Relay Networking & Synchronization

## 1. Multi-Relay Connection Pool
- Asynchronous WebSocket connection pool maintaining independent connections to multiple Nostr relays (`wss://relay.damus.io`, `wss://nos.lol`, `wss://relay.nostr.band`).
- Monitors ping latency (ms) and tracks errors per relay.

## 2. Offline-First Synchronization & Queue
- When internet connectivity is unavailable, posts and direct messages are saved to an offline queue in the local SQLite database (`stegstr.db`).
- Upon relay reconnection, queued events are automatically published across active relays.
