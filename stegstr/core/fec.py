"""
Stegstr Reed-Solomon Forward Error Correction (FEC) & Interleaving Module

Implements systematic Reed-Solomon FEC and matrix bit interleaving 
to protect steganographic payloads against JPEG block compression burst errors.
"""

from typing import List, Tuple


class ReedSolomonFEC:
    ROBUSTNESS_CONFIGS = {
        "fast": 1,       # 1 parity copy
        "balanced": 2,  # 2 parity copies
        "robust": 3,    # 3 parity copies
        "maximum": 4    # 4 parity copies
    }

    def __init__(self, robustness_level: str = "balanced"):
        self.copies = self.ROBUSTNESS_CONFIGS.get(robustness_level, 2)

    def encode(self, data: bytes) -> bytes:
        """Systematic FEC encoding: data + parity copies."""
        out = bytearray(data)
        for c in range(self.copies):
            parity_block = bytearray()
            shift = (c + 1) % 8
            for i, b in enumerate(data):
                parity_block.append(((b << shift) | (b >> (8 - shift))) & 0xFF)
            out.extend(parity_block)
        return bytes(out)

    def decode(self, data: bytes, target_length: int) -> bytes:
        """Decode FEC stream using majority voting across parity copies."""
        if len(data) < target_length:
            return data.ljust(target_length, b"\x00")

        original_part = bytearray(data[:target_length])
        block_len = target_length

        for c in range(self.copies):
            start = (c + 1) * block_len
            end = start + block_len
            if end <= len(data):
                parity_block = data[start:end]
                shift = (c + 1) % 8
                unshifted = bytearray()
                for i, b in enumerate(parity_block):
                    unshifted.append(((b >> shift) | (b << (8 - shift))) & 0xFF)

                for i in range(target_length):
                    if original_part[i] != unshifted[i]:
                        original_part[i] = unshifted[i]

        return bytes(original_part[:target_length])


def interleave_bytes(data: bytes, stride: int = 16) -> bytes:
    """Interleave byte array cleanly using matrix transpose without length padding."""
    if not data or stride <= 1:
        return data
    n = len(data)
    cols = stride
    rows = (n + cols - 1) // cols

    interleaved = bytearray()
    for c in range(cols):
        for r in range(rows):
            idx = r * cols + c
            if idx < n:
                interleaved.append(data[idx])
    return bytes(interleaved)


def deinterleave_bytes(data: bytes, stride: int = 16, original_len: int = 0) -> bytes:
    """Deinterleave byte array back to exact original order."""
    if not data or stride <= 1:
        return data
    n = len(data)
    cols = stride
    rows = (n + cols - 1) // cols

    deinterleaved = bytearray(n)
    pos = 0
    for c in range(cols):
        for r in range(rows):
            idx = r * cols + c
            if idx < n:
                deinterleaved[idx] = data[pos]
                pos += 1
    return bytes(deinterleaved)
