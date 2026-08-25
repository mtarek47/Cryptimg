"""
NIP-01 Nostr Event Handler & Protocol Specification

Implements canonical JSON event serialization, SHA256 event ID calculation,
event signing with BIP-340 Schnorr signatures, and signature verification.
"""

import json
import time
import hashlib
from typing import Dict, Any, List, Optional
from stegstr.nostr.keys import NostrKeyPair, sign_schnorr, verify_schnorr


class NostrEvent:
    def __init__(
        self,
        pubkey: str,
        kind: int,
        content: str,
        tags: Optional[List[List[str]]] = None,
        created_at: Optional[int] = None,
        id: Optional[str] = None,
        sig: Optional[str] = None
    ):
        self.pubkey = pubkey
        self.kind = kind
        self.content = content
        self.tags = tags or []
        self.created_at = created_at or int(time.time())
        self.id = id or self.calculate_id()
        self.sig = sig

    def serialize(self) -> str:
        """
        Canonical UTF-8 NIP-01 event payload serialization:
        [0, pubkey, created_at, kind, tags, content]
        """
        payload = [
            0,
            self.pubkey,
            self.created_at,
            self.kind,
            self.tags,
            self.content
        ]
        return json.dumps(payload, separators=(',', ':'), ensure_ascii=False)

    def calculate_id(self) -> str:
        """Compute SHA256 hash of canonical serialized event array."""
        serialized = self.serialize().encode('utf-8')
        return hashlib.sha256(serialized).hexdigest()

    def sign(self, private_key_hex: str):
        """Sign event with private key using BIP-340 Schnorr signature."""
        self.id = self.calculate_id()
        msg_hash = bytes.fromhex(self.id)
        self.sig = sign_schnorr(msg_hash, private_key_hex)

    def verify(self) -> bool:
        """Verify event ID hash and Schnorr signature."""
        if not self.id or not self.sig:
            return False
        if self.id != self.calculate_id():
            return False
        msg_hash = bytes.fromhex(self.id)
        return verify_schnorr(msg_hash, self.pubkey, self.sig)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "pubkey": self.pubkey,
            "created_at": self.created_at,
            "kind": self.kind,
            "tags": self.tags,
            "content": self.content,
            "sig": self.sig
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NostrEvent":
        return cls(
            pubkey=data["pubkey"],
            kind=data["kind"],
            content=data["content"],
            tags=data.get("tags", []),
            created_at=data.get("created_at"),
            id=data.get("id"),
            sig=data.get("sig")
        )

    @classmethod
    def create_text_note(cls, keypair: NostrKeyPair, content: str, tags: Optional[List[List[str]]] = None) -> "NostrEvent":
        """Create Kind 1 text note event."""
        evt = cls(
            pubkey=keypair.public_key_hex,
            kind=1,
            content=content,
            tags=tags or []
        )
        evt.sign(keypair.private_key_hex)
        return evt

    @classmethod
    def create_profile(cls, keypair: NostrKeyPair, name: str, about: str = "", picture: str = "") -> "NostrEvent":
        """Create Kind 0 metadata profile event."""
        content = json.dumps({"name": name, "about": about, "picture": picture})
        evt = cls(
            pubkey=keypair.public_key_hex,
            kind=0,
            content=content
        )
        evt.sign(keypair.private_key_hex)
        return evt
