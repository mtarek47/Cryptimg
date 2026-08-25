"""
Stegstr Compact Binary Protocol Specification & Codec

Provides compact binary packing for Nostr events and payload structures to minimize carrier capacity overhead.
"""

import struct
import zlib
import uuid
import time
from typing import Dict, Any, Optional, Tuple

MAGIC_V2 = b"STG2"
HEADER_FORMAT = "!4sBBB16sQ32s32sHHHI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
FOOTER_SIZE = 16 + 4

FLAG_COMPRESSED = 0x01
FLAG_ENCRYPTED = 0x02


class BinaryProtocolError(Exception):
    pass


class StegstrPacket:
    def __init__(
        self,
        mode: int = 0x02,
        flags: int = 0x01,
        message_id: Optional[bytes] = None,
        timestamp: Optional[int] = None,
        sender_pubkey: bytes = b"\x00" * 32,
        recipient_pubkey: bytes = b"\x00" * 32,
        frag_index: int = 0,
        frag_count: int = 1,
        fec_group: int = 0,
        payload: bytes = b"",
        auth_tag: bytes = b"\x00" * 16
    ):
        self.magic = MAGIC_V2
        self.version = 1
        self.mode = mode
        self.flags = flags
        self.message_id = message_id or uuid.uuid4().bytes
        self.timestamp = timestamp or int(time.time())
        
        if len(sender_pubkey) != 32:
            sender_pubkey = sender_pubkey.ljust(32, b"\x00")[:32]
        if len(recipient_pubkey) != 32:
            recipient_pubkey = recipient_pubkey.ljust(32, b"\x00")[:32]
            
        self.sender_pubkey = sender_pubkey
        self.recipient_pubkey = recipient_pubkey
        self.frag_index = frag_index
        self.frag_count = frag_count
        self.fec_group = fec_group
        self.payload = payload
        self.auth_tag = auth_tag.ljust(16, b"\x00")[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "magic": self.magic.decode('utf-8', errors='ignore'),
            "version": self.version,
            "mode": self.mode,
            "flags": self.flags,
            "message_id": self.message_id.hex(),
            "timestamp": self.timestamp,
            "sender_pubkey": self.sender_pubkey.hex(),
            "recipient_pubkey": self.recipient_pubkey.hex(),
            "frag_index": self.frag_index,
            "frag_count": self.frag_count,
            "fec_group": self.fec_group,
            "payload_size_bytes": len(self.payload)
        }

    def pack(self) -> bytes:
        payload_data = self.payload
        flags = self.flags

        if flags & FLAG_COMPRESSED:
            compressed = zlib.compress(payload_data, level=9)
            if len(compressed) < len(payload_data):
                payload_data = compressed
            else:
                flags &= ~FLAG_COMPRESSED

        payload_len = len(payload_data)
        
        header = struct.pack(
            HEADER_FORMAT,
            self.magic,
            self.version,
            self.mode,
            flags,
            self.message_id,
            self.timestamp,
            self.sender_pubkey,
            self.recipient_pubkey,
            self.frag_index,
            self.frag_count,
            self.fec_group,
            payload_len
        )

        body = header + payload_data + self.auth_tag
        crc = zlib.crc32(body) & 0xFFFFFFFF
        footer = struct.pack("!I", crc)

        return body + footer

    @classmethod
    def unpack(cls, data: bytes) -> "StegstrPacket":
        if len(data) < HEADER_SIZE + FOOTER_SIZE:
            raise BinaryProtocolError(f"Packet too short: {len(data)} bytes")

        header_bytes = data[:HEADER_SIZE]
        (
            magic,
            version,
            mode,
            flags,
            message_id,
            timestamp,
            sender_pubkey,
            recipient_pubkey,
            frag_index,
            frag_count,
            fec_group,
            payload_len
        ) = struct.unpack(HEADER_FORMAT, header_bytes)

        if magic != MAGIC_V2:
            raise BinaryProtocolError(f"Invalid magic header: {magic!r}")

        exact_packet_size = HEADER_SIZE + payload_len + 16 + 4
        if len(data) < exact_packet_size:
            raise BinaryProtocolError(f"Data truncated: expected {exact_packet_size} bytes, got {len(data)}")

        packet_bytes = data[:exact_packet_size]
        body = packet_bytes[:-4]
        crc_received = struct.unpack("!I", packet_bytes[-4:])[0]
        crc_calculated = zlib.crc32(body) & 0xFFFFFFFF

        if crc_received != crc_calculated:
            raise BinaryProtocolError(f"CRC32 mismatch: expected {hex(crc_calculated)}, got {hex(crc_received)}")

        raw_payload = body[HEADER_SIZE:HEADER_SIZE + payload_len]
        auth_tag = body[HEADER_SIZE + payload_len:HEADER_SIZE + payload_len + 16]

        if flags & FLAG_COMPRESSED:
            try:
                payload = zlib.decompress(raw_payload)
            except Exception as e:
                raise BinaryProtocolError(f"Decompression failed: {e}")
        else:
            payload = raw_payload

        return cls(
            mode=mode,
            flags=flags,
            message_id=message_id,
            timestamp=timestamp,
            sender_pubkey=sender_pubkey,
            recipient_pubkey=recipient_pubkey,
            frag_index=frag_index,
            frag_count=frag_count,
            fec_group=fec_group,
            payload=payload,
            auth_tag=auth_tag
        )
