"""
Carrier Quality Analyzer & Perceptual Metric Evaluator

Measures image texture complexity, available capacity, visual distortion (PSNR/SSIM),
and computes carrier quality scores and recommendation levels.
"""

import math
from typing import Dict, Any, Tuple
from PIL import Image
import numpy as np


def compute_psnr(original: Image.Image, stego: Image.Image) -> float:
    """Compute Peak Signal-to-Noise Ratio (PSNR) in dB between original and stego image."""
    arr1 = np.array(original.convert("RGB"), dtype=np.float32)
    arr2 = np.array(stego.convert("RGB"), dtype=np.float32)

    mse = float(np.mean((arr1 - arr2) ** 2))
    if mse == 0:
        return 100.0  # Infinite PSNR (identical images)

    max_pixel = 255.0
    psnr = 20.0 * math.log10(max_pixel / math.sqrt(mse))
    return float(psnr)


def compute_ssim(original: Image.Image, stego: Image.Image) -> float:
    """Compute simplified Structural Similarity Index (SSIM) between original and stego image."""
    img1 = np.array(original.convert("L"), dtype=np.float32)
    img2 = np.array(stego.convert("L"), dtype=np.float32)

    # Subsample if large to save memory and calculation time
    if img1.size > 500000:
        step = int(math.ceil(math.sqrt(img1.size / 250000)))
        img1 = img1[::step, ::step]
        img2 = img2[::step, ::step]

    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2

    mu1 = float(np.mean(img1))
    mu2 = float(np.mean(img2))

    sigma1_sq = float(np.var(img1))
    sigma2_sq = float(np.var(img2))
    
    # Fast covariance calculation without large matrix allocations
    f1 = img1.ravel() - mu1
    f2 = img2.ravel() - mu2
    sigma12 = float(np.mean(f1 * f2))

    num = (2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)
    den = (mu1 ** 2 + mu2 ** 2 + C1) * (sigma1_sq + sigma2_sq + C2)
    ssim = num / den if den != 0 else 1.0
    return float(np.clip(ssim, 0.0, 1.0))


def analyze_carrier(image: Image.Image) -> Dict[str, Any]:
    """
    Analyze image characteristics and compute steganographic carrier quality metrics.
    Returns structured analysis dictionary.
    """
    width, height = image.size
    total_pixels = width * height
    
    # Subsample large images for texture analysis to avoid huge memory allocations
    if total_pixels > 500000:
        thumb = image.copy()
        thumb.thumbnail((800, 800), Image.Resampling.BOX)
        gray = np.array(thumb.convert("L"), dtype=np.float32)
    else:
        gray = np.array(image.convert("L"), dtype=np.float32)
    
    # Fast Sobel gradients
    gx = np.abs(gray[:, 1:] - gray[:, :-1])
    gy = np.abs(gray[1:, :] - gray[:-1, :])
    texture_score = float((np.mean(gx) + np.mean(gy)) / 2.0)
    
    # 2. Capacity Estimates
    # Robust DCT capacity (8 bits per 8x8 block)
    blocks = (width // 8) * (height // 8)
    dct_capacity_bytes = blocks  # 1 byte per block
    png_capacity_bytes = (total_pixels * 3) // 8
    
    # 3. Robustness Rating
    if texture_score > 25.0:
        robustness_score = 92.0
        recommended_robustness = "robust"
    elif texture_score > 12.0:
        robustness_score = 85.0
        recommended_robustness = "balanced"
    else:
        robustness_score = 70.0
        recommended_robustness = "fast"
        
    recommended = "YES" if total_pixels >= 250000 else "CAUTION (Low Resolution)"
    
    return {
        "dimensions": f"{width}x{height}",
        "total_pixels": total_pixels,
        "texture_score": round(texture_score, 2),
        "capacity_dct_bytes": dct_capacity_bytes,
        "capacity_png_bytes": png_capacity_bytes,
        "robustness_score": round(robustness_score, 1),
        "visual_quality_score": 98.5 if texture_score > 15 else 95.0,
        "recommended_robustness": recommended_robustness,
        "recommended": recommended
    }
