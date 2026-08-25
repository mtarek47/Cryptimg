"""
Automated Media Transformation Test Harness & Steganographic Benchmark Suite

Simulates real-world media processing pipelines (JPEG compression, WebP conversion,
resizing, metadata stripping, repeated recompression) and measures payload bit error rates,
recovery rates, and visual quality scores (PSNR/SSIM).
"""

import io
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Union
from PIL import Image
import numpy as np

from stegstr.stego.engine import StegEngine
from stegstr.stego.carrier_analyzer import compute_psnr, compute_ssim
from stegstr.core.binary_protocol import StegstrPacket


def calculate_ber(original: bytes, recovered: bytes) -> float:
    """Calculate Bit Error Rate (BER) between original and recovered byte streams."""
    min_len = min(len(original), len(recovered))
    if min_len == 0:
        return 1.0

    total_bits = min_len * 8
    bit_errors = 0

    for i in range(min_len):
        diff = original[i] ^ recovered[i]
        bit_errors += bin(diff).count('1')

    length_diff_bits = abs(len(original) - len(recovered)) * 8
    total_bits += length_diff_bits
    bit_errors += length_diff_bits

    return float(bit_errors / total_bits)


def apply_transformation(img: Image.Image, transform_name: str) -> Image.Image:
    """Apply simulated platform media transformation pipeline to image."""
    buf = io.BytesIO()

    if transform_name == "original":
        return img.copy()

    elif transform_name.startswith("jpeg_q"):
        quality = int(transform_name.split("_q")[1])
        img.convert("RGB").save(buf, format="JPEG", quality=quality, subsampling=0)
        buf.seek(0)
        return Image.open(buf)

    elif transform_name == "resize_75":
        w, h = img.size
        resized = img.resize((int(w * 0.75), int(h * 0.75)), Image.Resampling.LANCZOS)
        resized.convert("RGB").save(buf, format="JPEG", quality=90)
        buf.seek(0)
        return Image.open(buf).resize((w, h), Image.Resampling.LANCZOS)

    elif transform_name == "resize_50":
        w, h = img.size
        resized = img.resize((int(w * 0.50), int(h * 0.50)), Image.Resampling.LANCZOS)
        resized.convert("RGB").save(buf, format="JPEG", quality=85)
        buf.seek(0)
        return Image.open(buf).resize((w, h), Image.Resampling.LANCZOS)

    elif transform_name == "webp":
        img.convert("RGB").save(buf, format="WEBP", quality=90)
        buf.seek(0)
        return Image.open(buf)

    elif transform_name == "jpeg_to_webp_to_jpeg":
        img.convert("RGB").save(buf, format="WEBP", quality=85)
        buf.seek(0)
        webp_img = Image.open(buf)
        buf2 = io.BytesIO()
        webp_img.convert("RGB").save(buf2, format="JPEG", quality=80)
        buf2.seek(0)
        return Image.open(buf2)

    elif transform_name == "metadata_stripped":
        arr = np.array(img.convert("RGB"), dtype=np.uint8)
        clean_img = Image.fromarray(arr, mode="RGB")
        clean_img.save(buf, format="JPEG", quality=95)
        buf.seek(0)
        return Image.open(buf)

    elif transform_name == "repeated_compression_3x":
        current = img.copy()
        for _ in range(3):
            b = io.BytesIO()
            current.convert("RGB").save(b, format="JPEG", quality=75)
            b.seek(0)
            current = Image.open(b)
        return current

    elif transform_name == "simulated_whatsapp":
        w, h = img.size
        max_dim = max(w, h)
        if max_dim > 1600:
            scale = 1600.0 / max_dim
            w_new, h_new = int(w * scale), int(h * scale)
            img_scaled = img.resize((w_new, h_new), Image.Resampling.LANCZOS)
        else:
            img_scaled = img.copy()
            w_new, h_new = w, h

        img_scaled.convert("RGB").save(buf, format="JPEG", quality=75, subsampling=1)
        buf.seek(0)
        return Image.open(buf).resize((w, h), Image.Resampling.LANCZOS)

    else:
        return img.copy()


def run_robustness_benchmark(image_input: Union[str, Path, Image.Image], robustness: str = "robust") -> Dict[str, Any]:
    """
    Run full media transformation benchmark suite across given carrier image.
    """
    if isinstance(image_input, (str, Path)):
        img = Image.open(image_input)
        img_name = str(image_input)
    else:
        img = image_input
        img_name = "memory_image"

    engine = StegEngine()
    test_payload = b"STEGSTR_CONTEST_BENCHMARK_PAYLOAD_32_BYTES_VERIFIED_OK!"

    enc_res = engine.encode(img, test_payload, mode="robust", robustness=robustness)
    stego_img = enc_res["stego_image"]
    psnr = enc_res["psnr_db"]
    ssim = enc_res["ssim"]

    transformations = [
        "original",
        "jpeg_q95",
        "jpeg_q85",
        "jpeg_q75",
        "jpeg_q60",
        "resize_75",
        "resize_50",
        "webp",
        "jpeg_to_webp_to_jpeg",
        "metadata_stripped",
        "repeated_compression_3x",
        "simulated_whatsapp"
    ]

    results = {}
    passed_count = 0

    for t_name in transformations:
        transformed_img = apply_transformation(stego_img, t_name)
        dec_res = engine.decode(transformed_img)

        if dec_res["status"] == "FOUND" and dec_res.get("payload"):
            rec_payload = dec_res["payload"]
            ber = calculate_ber(test_payload, rec_payload)
            is_pass = (ber == 0.0) or (test_payload in rec_payload)
        else:
            ber = 1.0
            is_pass = False

        if is_pass:
            passed_count += 1

        results[t_name] = {
            "pass": is_pass,
            "ber": round(ber, 4),
            "status": "PASS" if is_pass else "FAIL"
        }

    overall_robustness = round((passed_count / len(transformations)) * 100.0, 1)

    return {
        "timestamp": int(time.time()),
        "image": img_name,
        "codec": "Robust Mid-Frequency 2D-DCT QIM Codec",
        "overall_robustness": overall_robustness,
        "visual_quality": {
            "psnr_db": psnr,
            "ssim": ssim
        },
        "transformations": results
    }
