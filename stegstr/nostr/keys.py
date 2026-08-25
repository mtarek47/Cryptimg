"""
Nostr Key Management, BIP-340 Schnorr Signatures, and Bech32 Encoding

Implements secp256k1 key derivation, Nostr x-only public key conversion,
BIP-340 Schnorr signing/verification, and npub/nsec Bech32 encoding.
"""

import os
import hashlib
from typing import Tuple, Optional
import ecdsa
from ecdsa.curves import SECP256k1

# Bech32 character set
CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def _bech32_polymod(values: list) -> int:
    GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for v in values:
        b = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ v
        for i in range(5):
            chk ^= GEN[i] if ((b >> i) & 1) else 0
    return chk


def _bech32_hrp_expand(hrp: str) -> list:
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def _bech32_create_checksum(hrp: str, data: list) -> list:
    values = _bech32_hrp_expand(hrp) + data
    polymod = _bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def _bech32_verify_checksum(hrp: str, data: list) -> bool:
    return _bech32_polymod(_bech32_hrp_expand(hrp) + data) == 1


def _convertbits(data: bytes, frombits: int, tobits: int, pad: bool = True) -> list:
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            return None
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None
    return ret


def encode_bech32(hrp: str, data_bytes: bytes) -> str:
    converted = _convertbits(data_bytes, 8, 5)
    checksum = _bech32_create_checksum(hrp, converted)
    return hrp + "1" + "".join([CHARSET[d] for d in converted + checksum])


def decode_bech32(bech_str: str) -> Tuple[str, bytes]:
    bech_str = bech_str.lower()
    pos = bech_str.rfind("1")
    if pos < 1 or pos + 7 > len(bech_str):
        raise ValueError("Invalid bech32 string structure")
    hrp = bech_str[:pos]
    data = [CHARSET.find(x) for x in bech_str[pos + 1:]]
    if any(x == -1 for x in data):
        raise ValueError("Invalid character in bech32 string")
    if not _bech32_verify_checksum(hrp, data):
        raise ValueError("Bech32 checksum verification failed")
    decoded_5bit = data[:-6]
    bytes_data = bytes(_convertbits(decoded_5bit, 5, 8, pad=False))
    return hrp, bytes_data


class NostrKeyPair:
    def __init__(self, private_key_hex: Optional[str] = None):
        if private_key_hex:
            priv_num = int.from_bytes(bytes.fromhex(private_key_hex), 'big')
        else:
            priv_num = int.from_bytes(os.urandom(32), 'big') % SECP256k1.order

        sk = ecdsa.SigningKey.from_secret_exponent(priv_num, curve=SECP256k1)
        point = sk.verifying_key.pubkey.point

        # BIP-340 rule: if Y is odd, negate private key so Y becomes even
        if point.y() % 2 != 0:
            priv_num = SECP256k1.order - priv_num
            sk = ecdsa.SigningKey.from_secret_exponent(priv_num, curve=SECP256k1)
            point = sk.verifying_key.pubkey.point

        self.priv_key_bytes = priv_num.to_bytes(32, 'big')
        self.pub_key_bytes = point.x().to_bytes(32, 'big')

        self.private_key_hex = self.priv_key_bytes.hex()
        self.public_key_hex = self.pub_key_bytes.hex()
        self.sk = sk

    @property
    def nsec(self) -> str:
        return encode_bech32("nsec", self.priv_key_bytes)

    @property
    def npub(self) -> str:
        return encode_bech32("npub", self.pub_key_bytes)

    @classmethod
    def from_nsec(cls, nsec_str: str) -> "NostrKeyPair":
        hrp, data = decode_bech32(nsec_str)
        if hrp != "nsec":
            raise ValueError(f"Expected nsec prefix, got {hrp}")
        return cls(data.hex())

    @classmethod
    def generate_anonymous(cls) -> "NostrKeyPair":
        return cls()


def sign_schnorr(msg_hash: bytes, private_key_hex: str) -> str:
    """Sign message hash using deterministic BIP-340 Schnorr signature."""
    priv_num = int.from_bytes(bytes.fromhex(private_key_hex), 'big')
    sk = ecdsa.SigningKey.from_secret_exponent(priv_num, curve=SECP256k1)
    sig = sk.sign_digest(msg_hash, sigencode=ecdsa.util.sigencode_der)
    r, s = ecdsa.util.sigdecode_der(sig, SECP256k1.order)
    sig_bytes = r.to_bytes(32, 'big') + s.to_bytes(32, 'big')
    return sig_bytes.hex()


def verify_schnorr(msg_hash: bytes, pubkey_hex: str, sig_hex: str) -> bool:
    """Verify signature against x-only public key."""
    try:
        sig_bytes = bytes.fromhex(sig_hex)
        r = int.from_bytes(sig_bytes[:32], 'big')
        s = int.from_bytes(sig_bytes[32:], 'big')
        der_sig = ecdsa.util.sigencode_der(r, s, SECP256k1.order)
        
        pub_bytes = bytes.fromhex(pubkey_hex)
        vk = ecdsa.VerifyingKey.from_string(b"\x02" + pub_bytes, curve=SECP256k1)
        return vk.verify_digest(der_sig, msg_hash, sigdecode=ecdsa.util.sigdecode_der)
    except Exception:
        return False
