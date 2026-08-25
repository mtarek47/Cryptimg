"""
Legacy PNG Spatial LSB Steganography Codec

Maintains 100% compatibility with original Stegstr PNG LSB payload structure:
Magic: STEGSTR (7 bytes) + Big-Endian Length (4 bytes) + Payload Bytes.
"""

import struct
from typing import Dict, Any, Optional
from PIL import Image
import numpy as np

from stegstr.stego.codecs.base import BaseStegoCodec, StegoCodecError
from stegstr.config import LEGACY_MAGIC, MODE_LEGACY_PNG


class LosslessPNGCodec(BaseStegoCodec):
    @property
    def mode_id(self) -> int:
        return MODE_LEGACY_PNG

    @property
    def name(self) -> str:
        return "Legacy PNG LSB Codec"

    def estimate_capacity(self, image: Image.Image, parameters: Optional[Dict[str, Any]] = None) -> int:
        width, height = image.size
        # 3 channels (RGB), 1 bit per channel = (width * height * 3) / 8 bytes total raw capacity
        raw_capacity = (width * height * 3) // 8
        header_len = len(LEGACY_MAGIC) + 4
        return max(0, raw_capacity - header_len)

    def encode(self, image: Image.Image, payload: bytes, parameters: Optional[Dict[str, Any]] = None) -> Image.Image:
        if image.mode != "RGB":
            image = image.convert("RGB")

        capacity = self.estimate_capacity(image)
        if len(payload) > capacity:
            raise StegoCodecError(f"Payload size ({len(payload)} B) exceeds PNG LSB capacity ({capacity} B)")

        # Prepare legacy stream: STEGSTR + uint32_be(len) + payload
        full_stream = LEGACY_MAGIC + struct.pack("!I", len(payload)) + payload

        # Convert payload bytes to bit array
        bits = []
        for b in full_stream:
            for bit_idx in range(7, -1, -1):
                bits.append((b >> bit_idx) & 1)

        img_arr = np.array(image, dtype=np.uint8)
        flat = img_arr.flatten()

        if len(bits) > len(flat):
            raise StegoCodecError("Image too small to hold bitstream")

        # Clear LSB and set bit
        flat[:len(bits)] = (flat[:len(bits)] & 0xFE) | np.array(bits, dtype=np.uint8)

        stego_arr = flat.reshape(img_arr.shape)
        return Image.fromarray(stego_arr, mode="RGB")

    def decode(self, image: Image.Image, parameters: Optional[Dict[str, Any]] = None) -> bytes:
        if image.mode != "RGB":
            image = image.convert("RGB")

        img_arr = np.array(image, dtype=np.uint8)
        flat = img_arr.flatten()

        # Extract bits from LSB
        lsb_bits = flat & 1

        # Helper to extract N bytes from bit stream
        def extract_bytes(start_bit: int, num_bytes: int) -> bytes:
            out = bytearray()
            for b_idx in range(num_bytes):
                byte_val = 0
                for bit_idx in range(8):
                    pos = start_bit + b_idx * 8 + bit_idx
                    if pos >= len(lsb_bits):
                        raise StegoCodecError("Premature end of LSB bitstream")
                    byte_val = (byte_val << 1) | int(lsb_bits[pos])
                out.append(byte_val)
            return bytes(out)

        # 1. Read legacy magic header
        magic_len = len(LEGACY_MAGIC)
        header = extract_bytes(0, magic_len)
        if header != LEGACY_MAGIC:
            raise StegoCodecError(f"Invalid legacy magic header: {header!r}")

        # 2. Read uint32_be length
        len_bytes = extract_bytes(magic_len * 8, 4)
        payload_len = struct.unpack("!I", len_bytes)[0]

        # 3. Read payload bytes
        start_payload_bit = (magic_len + 4) * 8
        payload = extract_bytes(start_payload_bit, payload_len)
        return payload
