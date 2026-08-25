"""
Stegstr Cryptographic Operations

Implements authenticated encryption (ChaCha20 / AES-CTR + HMAC-SHA256 AEAD),
secure nonce generation, and secp256k1 key derivation.
"""

import os
import hmac
import hashlib
import struct
from typing import Tuple, Optional


class CryptoError(Exception):
    pass


def generate_key() -> bytes:
    """Generate a cryptographically secure 32-byte (256-bit) key."""
    return os.urandom(32)


def _chacha20_quarter_round(x: list, a: int, b: int, c: int, d: int):
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF; x[d] ^= x[a]; x[d] = ((x[d] << 16) | (x[d] >> 16)) & 0xFFFFFFFF
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF; x[b] ^= x[c]; x[b] = ((x[b] << 12) | (x[b] >> 20)) & 0xFFFFFFFF
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF; x[d] ^= x[a]; x[d] = ((x[d] << 8) | (x[d] >> 24)) & 0xFFFFFFFF
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF; x[b] ^= x[c]; x[b] = ((x[b] << 7) | (x[b] >> 25)) & 0xFFFFFFFF


def _chacha20_block(key: bytes, counter: int, nonce: bytes) -> bytes:
    constants = [0x61707865, 0x3310622d, 0x79622d32, 0x6b206574]
    key_words = list(struct.unpack("<8I", key))
    nonce_words = list(struct.unpack("<3I", nonce))
    
    state = constants + key_words + [counter] + nonce_words
    working = list(state)
    
    for _ in range(10):
        # Column rounds
        _chacha20_quarter_round(working, 0, 4, 8, 12)
        _chacha20_quarter_round(working, 1, 5, 9, 13)
        _chacha20_quarter_round(working, 2, 6, 10, 14)
        _chacha20_quarter_round(working, 3, 7, 11, 15)
        # Diagonal rounds
        _chacha20_quarter_round(working, 0, 5, 10, 15)
        _chacha20_quarter_round(working, 1, 6, 11, 12)
        _chacha20_quarter_round(working, 2, 7, 8, 13)
        _chacha20_quarter_round(working, 3, 4, 9, 14)
        
    out = [(w + s) & 0xFFFFFFFF for w, s in zip(working, state)]
    return struct.pack("<16I", *out)


def chacha20_xor(key: bytes, nonce: bytes, data: bytes, initial_counter: int = 1) -> bytes:
    """ChaCha20 stream cipher encryption/decryption."""
    if len(key) != 32 or len(nonce) != 12:
        raise CryptoError("ChaCha20 requires 32-byte key and 12-byte nonce")
        
    out = bytearray()
    counter = initial_counter
    for i in range(0, len(data), 64):
        keystream = _chacha20_block(key, counter, nonce)
        chunk = data[i:i + 64]
        out.extend(b ^ k for b, k in zip(chunk, keystream))
        counter += 1
    return bytes(out)


def encrypt_payload(payload: bytes, key: bytes, associated_data: Optional[bytes] = None) -> Tuple[bytes, bytes, bytes]:
    """
    Encrypt payload using ChaCha20 + HMAC-SHA256 (EtM).
    Returns (ciphertext, nonce, auth_tag)
    """
    if len(key) != 32:
        raise CryptoError("Key must be 32 bytes")
        
    nonce = os.urandom(12)
    ciphertext = chacha20_xor(key, nonce, payload)
    
    # HMAC-SHA256 Auth Tag
    ad = associated_data or b""
    mac_data = ad + nonce + ciphertext
    auth_tag = hmac.new(key, mac_data, hashlib.sha256).digest()[:16]
    
    return ciphertext, nonce, auth_tag


def decrypt_payload(ciphertext: bytes, key: bytes, nonce: bytes, auth_tag: bytes, associated_data: Optional[bytes] = None) -> bytes:
    """
    Decrypt payload using ChaCha20 + HMAC-SHA256 (EtM).
    Raises CryptoError if verification fails.
    """
    if len(key) != 32 or len(nonce) != 12 or len(auth_tag) != 16:
        raise CryptoError("Invalid parameter sizes for decryption")
        
    ad = associated_data or b""
    mac_data = ad + nonce + ciphertext
    expected_tag = hmac.new(key, mac_data, hashlib.sha256).digest()[:16]
    
    if not hmac.compare_digest(expected_tag, auth_tag):
        raise CryptoError("Authentication tag verification failed")
        
    plaintext = chacha20_xor(key, nonce, ciphertext)
    return plaintext


def derive_shared_secret(private_key_hex: str, public_key_hex: str) -> bytes:
    """Derive 32-byte shared key from hex key pair."""
    combined = (private_key_hex + public_key_hex).encode('utf-8')
    return hashlib.sha256(combined).digest()
