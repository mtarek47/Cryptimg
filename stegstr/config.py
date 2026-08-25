"""
Stegstr Configuration & System Constants
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("STEGSTR_DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "stegstr.db"

# Default Nostr Relays
DEFAULT_RELAYS = [
    "wss://relay.damus.io",
    "wss://nos.lol",
    "wss://relay.nostr.band",
    "wss://nostr.mom"
]

# Steganography Defaults
DEFAULT_ROBUSTNESS_LEVEL = "balanced"  # fast, balanced, robust, maximum
MAGIC_HEADER = b"STG2"  # 4 bytes for Stegstr V2
LEGACY_MAGIC = b"STEGSTR"  # 7 bytes for Stegstr V1 (legacy PNG)

# Codec Modes
MODE_LEGACY_PNG = 0x01
MODE_ROBUST_DCT = 0x02

# Robust DCT Parameters
DCT_BLOCK_SIZE = 8
DEFAULT_QUANT_STEP = 32.0  # Base quantization step size delta for robust QIM

# Server Defaults
API_HOST = "0.0.0.0"
API_PORT = 8765
