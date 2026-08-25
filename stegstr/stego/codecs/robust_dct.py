"""
Robust 2D-DCT Quantization Index Modulation (QIM) Steganography Codec

Transformation-resistant steganography codec operating on mid-frequency DCT 
coefficients of the Luminance (Y) channel. Designed to survive lossy JPEG compression, 
WebP transcode, resolution scaling, and metadata stripping.
"""

import math
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image
import numpy as np

from stegstr.stego.codecs.base import BaseStegoCodec, StegoCodecError
from stegstr.config import MODE_ROBUST_DCT, DEFAULT_QUANT_STEP

# Precompute 8x8 DCT-II Basis Matrix
DCT_MATRIX = np.zeros((8, 8), dtype=np.float64)
for i in range(8):
    alpha = math.sqrt(1.0 / 8.0) if i == 0 else math.sqrt(2.0 / 8.0)
    for j in range(8):
        DCT_MATRIX[i, j] = alpha * math.cos((math.pi * (2 * j + 1) * i) / 16.0)

DCT_MATRIX_T = DCT_MATRIX.T

# Mid-frequency DCT coefficient positions in 8x8 block (survives JPEG quantization)
MID_FREQ_POSITIONS = [
    (3, 2), (2, 3), (4, 1), (1, 4),
    (3, 3), (2, 4), (4, 2), (3, 4)
]


def dct2d(block: np.ndarray) -> np.ndarray:
    return np.dot(np.dot(DCT_MATRIX, block), DCT_MATRIX_T)


def idct2d(block: np.ndarray) -> np.ndarray:
    return np.dot(np.dot(DCT_MATRIX_T, block), DCT_MATRIX)


class RobustDCTCodec(BaseStegoCodec):
    @property
    def mode_id(self) -> int:
        return MODE_ROBUST_DCT

    @property
    def name(self) -> str:
        return "Robust Mid-Frequency 2D-DCT QIM Codec"

    def estimate_capacity(self, image: Image.Image, parameters: Optional[Dict[str, Any]] = None) -> int:
        width, height = image.size
        num_blocks = (width // 8) * (height // 8)
        bits_per_block = len(MID_FREQ_POSITIONS)
        total_bits = num_blocks * bits_per_block
        return total_bits // 8

    def _rgb_to_ycbcr(self, img: Image.Image) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        arr = np.array(img.convert("RGB"), dtype=np.float64)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        
        y = 0.299 * r + 0.587 * g + 0.114 * b
        cb = 128 - 0.168736 * r - 0.331264 * g + 0.5 * b
        cr = 128 + 0.5 * r - 0.418688 * g - 0.081312 * b
        return y, cb, cr

    def _ycbcr_to_rgb(self, y: np.ndarray, cb: np.ndarray, cr: np.ndarray) -> Image.Image:
        r = y + 1.402 * (cr - 128)
        g = y - 0.344136 * (cb - 128) - 0.714136 * (cr - 128)
        b = y + 1.772 * (cb - 128)
        
        rgb = np.stack([r, g, b], axis=-1)
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)
        return Image.fromarray(rgb, mode="RGB")

    def encode(self, image: Image.Image, payload: bytes, parameters: Optional[Dict[str, Any]] = None) -> Image.Image:
        parameters = parameters or {}
        delta = float(parameters.get("quant_step", DEFAULT_QUANT_STEP))

        y, cb, cr = self._rgb_to_ycbcr(image)
        h, w = y.shape
        blocks_h = h // 8
        blocks_w = w // 8

        total_blocks = blocks_h * blocks_w
        max_bits = total_blocks * len(MID_FREQ_POSITIONS)

        # Convert payload to bit array
        payload_bits = []
        for byte in payload:
            for bit_idx in range(7, -1, -1):
                payload_bits.append((byte >> bit_idx) & 1)

        if len(payload_bits) > max_bits:
            raise StegoCodecError(f"Payload ({len(payload_bits)} bits) exceeds DCT capacity ({max_bits} bits)")

        bit_cursor = 0
        total_payload_bits = len(payload_bits)
        y_mod = y.copy()

        for bh in range(blocks_h):
            for bw in range(blocks_w):
                if bit_cursor >= total_payload_bits:
                    break

                block = y_mod[bh * 8:(bh + 1) * 8, bw * 8:(bw + 1) * 8] - 128.0
                dct_block = dct2d(block)

                for u, v in MID_FREQ_POSITIONS:
                    if bit_cursor >= total_payload_bits:
                        break

                    bit = payload_bits[bit_cursor]
                    coeff = dct_block[u, v]

                    # Quantization Index Modulation (QIM)
                    # Embed bit b: C' = round((C - b*delta/2)/delta)*delta + b*delta/2
                    k = round((coeff - bit * (delta / 2.0)) / delta)
                    quant_coeff = k * delta + bit * (delta / 2.0)

                    dct_block[u, v] = quant_coeff
                    bit_cursor += 1

                idct_block = idct2d(dct_block) + 128.0
                y_mod[bh * 8:(bh + 1) * 8, bw * 8:(bw + 1) * 8] = idct_block

            if bit_cursor >= total_payload_bits:
                break

        return self._ycbcr_to_rgb(y_mod, cb, cr)

    def decode(self, image: Image.Image, parameters: Optional[Dict[str, Any]] = None) -> bytes:
        parameters = parameters or {}
        delta = float(parameters.get("quant_step", DEFAULT_QUANT_STEP))
        expected_len = parameters.get("expected_len", None)

        y, _, _ = self._rgb_to_ycbcr(image)
        h, w = y.shape
        blocks_h = h // 8
        blocks_w = w // 8

        extracted_bits = []

        for bh in range(blocks_h):
            for bw in range(blocks_w):
                block = y[bh * 8:(bh + 1) * 8, bw * 8:(bw + 1) * 8] - 128.0
                dct_block = dct2d(block)

                for u, v in MID_FREQ_POSITIONS:
                    coeff = dct_block[u, v]

                    # QIM Distance comparison
                    # Distance to bit=0 center vs bit=1 center
                    c0 = round(coeff / delta) * delta
                    c1 = round((coeff - delta / 2.0) / delta) * delta + delta / 2.0

                    d0 = abs(coeff - c0)
                    d1 = abs(coeff - c1)

                    bit = 0 if d0 < d1 else 1
                    extracted_bits.append(bit)

                    if expected_len and len(extracted_bits) >= expected_len * 8:
                        break

                if expected_len and len(extracted_bits) >= expected_len * 8:
                    break
            if expected_len and len(extracted_bits) >= expected_len * 8:
                break

        # Convert bits to bytes
        out_bytes = bytearray()
        for i in range(0, len(extracted_bits) - 7, 8):
            byte_val = 0
            for b in range(8):
                byte_val = (byte_val << 1) | extracted_bits[i + b]
            out_bytes.append(byte_val)

        return bytes(out_bytes)
