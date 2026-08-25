"""
StegEngine Unified Steganographic Engine & Detection Scanner

Orchestrates automatic codec selection, FEC application, binary protocol packing,
multi-codec detection scanning, and legacy PNG compatibility fallback.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from PIL import Image

from stegstr.stego.codecs.base import BaseStegoCodec, StegoCodecError
from stegstr.stego.codecs.lsb_png import LosslessPNGCodec
from stegstr.stego.codecs.robust_dct import RobustDCTCodec
from stegstr.stego.carrier_analyzer import analyze_carrier, compute_psnr, compute_ssim
from stegstr.core.binary_protocol import StegstrPacket, BinaryProtocolError
from stegstr.core.fec import ReedSolomonFEC, interleave_bytes, deinterleave_bytes
from stegstr.config import MODE_LEGACY_PNG, MODE_ROBUST_DCT, LEGACY_MAGIC, MAGIC_HEADER

ROBUSTNESS_FLAG_MAP = {
    "fast": 0x00,
    "balanced": 0x04,
    "robust": 0x08,
    "maximum": 0x0C
}

FLAG_ROBUSTNESS_REVERSE_MAP = {
    0x00: "fast",
    0x04: "balanced",
    0x08: "robust",
    0x0C: "maximum"
}

QUANT_STEP_MAP = {
    "fast": 24.0,
    "balanced": 32.0,
    "robust": 48.0,
    "maximum": 64.0
}


class StegEngine:
    def __init__(self):
        self.codecs: Dict[int, BaseStegoCodec] = {
            MODE_LEGACY_PNG: LosslessPNGCodec(),
            MODE_ROBUST_DCT: RobustDCTCodec()
        }

    def encode(
        self,
        image_input: Union[str, Path, Image.Image],
        payload: bytes,
        mode: str = "auto",
        robustness: str = "balanced",
        output_path: Optional[Union[str, Path]] = None,
        encryption_key: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Embed binary payload into carrier image using selected or automatic steganography codec.
        """
        if isinstance(image_input, (str, Path)):
            img = Image.open(image_input)
            src_path = str(image_input)
        else:
            img = image_input
            src_path = "memory"

        analysis = analyze_carrier(img)

        if mode == "auto":
            if robustness == "fast" and src_path.lower().endswith(".png"):
                selected_codec_id = MODE_LEGACY_PNG
            else:
                selected_codec_id = MODE_ROBUST_DCT
        elif mode == "legacy" or mode == "png":
            selected_codec_id = MODE_LEGACY_PNG
        else:
            selected_codec_id = MODE_ROBUST_DCT

        codec = self.codecs[selected_codec_id]
        rob_flag = ROBUSTNESS_FLAG_MAP.get(robustness, 0x04)
        quant_step = QUANT_STEP_MAP.get(robustness, 32.0)

        if selected_codec_id == MODE_ROBUST_DCT:
            fec = ReedSolomonFEC(robustness_level=robustness)
            fec_payload = fec.encode(payload)
            interleaved_payload = interleave_bytes(fec_payload, stride=16)
            
            packet = StegstrPacket(
                mode=MODE_ROBUST_DCT,
                flags=0x01 | rob_flag,
                payload=interleaved_payload
            )
            raw_stream = packet.pack()
            stego_img = codec.encode(img, raw_stream, parameters={"quant_step": quant_step})
        else:
            packet = StegstrPacket(
                mode=MODE_LEGACY_PNG,
                flags=0x01 | rob_flag,
                payload=payload
            )
            raw_stream = packet.pack()
            stego_img = codec.encode(img, raw_stream)

        psnr = compute_psnr(img, stego_img)
        ssim = compute_ssim(img, stego_img)

        saved_path = None
        if output_path:
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            
            if selected_codec_id == MODE_LEGACY_PNG or str(output_path).lower().endswith(".png"):
                stego_img.save(output_path, format="PNG")
            else:
                stego_img.save(output_path, format="JPEG", quality=95, subsampling=0)
            saved_path = str(output_path)

        return {
            "status": "SUCCESS",
            "codec": codec.name,
            "mode": mode,
            "robustness": robustness,
            "payload_size_bytes": len(payload),
            "total_stream_bytes": len(raw_stream),
            "psnr_db": round(psnr, 2),
            "ssim": round(ssim, 4),
            "output_path": saved_path,
            "carrier_analysis": analysis,
            "stego_image": stego_img
        }

    def decode(
        self,
        image_input: Union[str, Path, Image.Image],
        compat: bool = True,
        encryption_key: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Detect and extract hidden payload from carrier image with legacy fallback chain.
        """
        if isinstance(image_input, (str, Path)):
            img = Image.open(image_input)
            src_name = str(image_input)
        else:
            img = image_input
            src_name = "memory"

        # Step 1: Try Robust DCT Codec with multiple candidate quantization steps
        dct_codec = self.codecs[MODE_ROBUST_DCT]
        for q_step in [32.0, 48.0, 64.0, 24.0]:
            try:
                extracted_raw = dct_codec.decode(img, parameters={"quant_step": q_step})
                
                if MAGIC_HEADER in extracted_raw:
                    idx = extracted_raw.find(MAGIC_HEADER)
                    packet_data = extracted_raw[idx:]
                    packet = StegstrPacket.unpack(packet_data)
                    
                    rob_bits = packet.flags & 0x0C
                    robustness_level = FLAG_ROBUSTNESS_REVERSE_MAP.get(rob_bits, "balanced")
                    
                    fec = ReedSolomonFEC(robustness_level=robustness_level)
                    deinterleaved = deinterleave_bytes(packet.payload, stride=16)
                    
                    target_len = len(deinterleaved) // (fec.copies + 1)
                    try:
                        payload = fec.decode(deinterleaved, target_length=target_len)
                        payload = payload.rstrip(b"\x00")
                    except Exception:
                        payload = packet.payload

                    return {
                        "status": "FOUND",
                        "codec": dct_codec.name,
                        "packet": packet,
                        "payload": payload,
                        "source": src_name
                    }
            except Exception:
                continue

        # Step 2: Try Legacy PNG Codec if compat mode enabled
        if compat:
            try:
                png_codec = self.codecs[MODE_LEGACY_PNG]
                legacy_raw = png_codec.decode(img)
                
                if MAGIC_HEADER in legacy_raw:
                    idx = legacy_raw.find(MAGIC_HEADER)
                    packet = StegstrPacket.unpack(legacy_raw[idx:])
                    return {
                        "status": "FOUND",
                        "codec": "Legacy PNG Codec (V2 Packet)",
                        "packet": packet,
                        "payload": packet.payload,
                        "source": src_name
                    }
                else:
                    return {
                        "status": "FOUND",
                        "codec": png_codec.name,
                        "packet": None,
                        "payload": legacy_raw,
                        "source": src_name
                    }
            except Exception:
                pass

        return {
            "status": "NONE",
            "codec": None,
            "payload": None,
            "source": src_name,
            "error": "No Stegstr payload detected"
        }

    def detect(self, target_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Scan a single file or directory of image files for Stegstr payloads.
        """
        target = Path(target_path)
        results = []

        if target.is_file():
            files = [target]
        elif target.is_dir():
            files = [p for p in target.glob("*") if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
        else:
            return [{"source": str(target_path), "status": "ERROR", "error": "Path does not exist"}]

        for f in files:
            try:
                res = self.decode(f)
                results.append({
                    "file": str(f),
                    "filename": f.name,
                    "status": res["status"],
                    "codec": res.get("codec"),
                    "payload_len": len(res["payload"]) if res.get("payload") else 0
                })
            except Exception as e:
                results.append({
                    "file": str(f),
                    "filename": f.name,
                    "status": "CORRUPTED",
                    "error": str(e)
                })

        return results
