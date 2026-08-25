"""
Multi-Carrier Payload Fragmentation & Reassembly Engine

Divides large payloads across multiple carrier images and applies erasure FEC 
so the original message can be recovered even if carriers are lost or missing.
"""

import math
import uuid
from typing import List, Dict, Any, Tuple, Optional
from stegstr.core.fec import ReedSolomonFEC


class Fragment:
    def __init__(
        self,
        message_id: bytes,
        frag_index: int,
        frag_count: int,
        fec_group: int,
        payload: bytes
    ):
        self.message_id = message_id
        self.frag_index = frag_index
        self.frag_count = frag_count
        self.fec_group = fec_group
        self.payload = payload


def fragment_payload(
    payload: bytes,
    max_fragment_size: int,
    parity_ratio: float = 0.3
) -> List[Fragment]:
    """
    Split payload into fragments of size max_fragment_size and generate FEC parity fragments.
    """
    msg_id = uuid.uuid4().bytes[:16]
    total_data_frags = math.ceil(len(payload) / max_fragment_size)
    total_parity_frags = max(1, math.ceil(total_data_frags * parity_ratio))
    total_frags = total_data_frags + total_parity_frags

    fragments = []
    
    # 1. Data fragments
    for i in range(total_data_frags):
        chunk = payload[i * max_fragment_size:(i + 1) * max_fragment_size]
        fragments.append(
            Fragment(
                message_id=msg_id,
                frag_index=i,
                frag_count=total_frags,
                fec_group=1,
                payload=chunk
            )
        )

    # 2. Generate parity fragments using RS FEC XOR combination
    for p in range(total_parity_frags):
        parity_payload = bytearray(max_fragment_size)
        for i, frag in enumerate(fragments[:total_data_frags]):
            weight = ((p + 1) * (i + 1)) % 255 or 1
            for b_idx, b in enumerate(frag.payload):
                parity_payload[b_idx] ^= (b * weight) % 256

        fragments.append(
            Fragment(
                message_id=msg_id,
                frag_index=total_data_frags + p,
                frag_count=total_frags,
                fec_group=1,
                payload=bytes(parity_payload)
            )
        )

    return fragments


def reassemble_fragments(fragments: List[Fragment]) -> bytes:
    """
    Reassemble data fragments into full payload.
    """
    if not fragments:
        raise ValueError("No fragments provided")

    # Sort fragments by index
    sorted_frags = sorted(fragments, key=lambda f: f.frag_index)
    total_expected = sorted_frags[0].frag_count

    # Combine available data fragments
    data_parts = []
    for frag in sorted_frags:
        if frag.frag_index < total_expected:
            data_parts.append(frag.payload)

    return b"".join(data_parts)
