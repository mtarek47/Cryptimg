"""
Synchronization Markers & Barker/Gold Code Sequences

Provides visual anchor detection and alignment pattern matching for cropped or 
rescaled carrier images.
"""

from typing import List, Tuple
import numpy as np

# 13-bit Barker Code sequence: +1, +1, +1, +1, +1, -1, -1, +1, +1, -1, +1, -1, +1
BARKER_13 = np.array([1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1], dtype=np.float64)


def embed_sync_marker(block_dc: float, delta: float) -> float:
    """Modulate DC coefficient to embed a synchronization pulse."""
    return round(block_dc / delta) * delta + (delta * 0.25)


def correlate_sync_marker(signal: np.ndarray) -> np.ndarray:
    """Compute normalized cross-correlation of signal against Barker-13 sequence."""
    if len(signal) < len(BARKER_13):
        return np.array([0.0])
    corr = np.correlate(signal, BARKER_13, mode='valid')
    norm = np.sqrt(np.sum(BARKER_13 ** 2) * np.convolve(signal ** 2, np.ones(len(BARKER_13)), mode='valid'))
    norm[norm == 0] = 1.0
    return corr / norm
