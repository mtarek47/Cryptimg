"""
NIP-04 / NIP-44 Nostr Direct Messaging Encryption

Handles key agreement and payload encryption for Kind 4 Direct Messages.
"""

import base64
import os
from typing import Tuple
from stegstr.core.crypto import encrypt_payload, decrypt_payload, derive_shared_secret
from stegstr.nostr.events import NostrEvent
from stegstr.nostr.keys import NostrKeyPair, decode_bech32


def encrypt_dm(
    sender_keypair: NostrKeyPair,
    recipient_pubkey: str,
    message: str
) -> NostrEvent:
    """
    Encrypt direct message and create Kind 4 Nostr event.
    Accepts recipient_pubkey as hex string or npub1... Bech32 string.
    """
    if recipient_pubkey.startswith("npub1"):
        _, data = decode_bech32(recipient_pubkey)
        recipient_pubkey_hex = data.hex()
    else:
        recipient_pubkey_hex = recipient_pubkey

    shared_secret = derive_shared_secret(sender_keypair.private_key_hex, recipient_pubkey_hex)
    ciphertext, nonce, auth_tag = encrypt_payload(message.encode('utf-8'), shared_secret)

    payload_b64 = base64.b64encode(ciphertext + auth_tag).decode('utf-8')
    iv_b64 = base64.b64encode(nonce).decode('utf-8')
    content = f"{payload_b64}?iv={iv_b64}"

    tags = [["p", recipient_pubkey_hex]]
    evt = NostrEvent(
        pubkey=sender_keypair.public_key_hex,
        kind=4,
        content=content,
        tags=tags
    )
    evt.sign(sender_keypair.private_key_hex)
    return evt


def decrypt_dm(
    active_keypair: NostrKeyPair,
    event: NostrEvent
) -> str:
    """
    Decrypt Kind 4 Nostr direct message event for either sender or recipient.
    """
    if event.kind != 4:
        raise ValueError(f"Expected Kind 4 event, got {event.kind}")

    if active_keypair.public_key_hex == event.pubkey:
        # Active keypair is the SENDER
        if event.tags and len(event.tags[0]) > 1:
            other_pubkey_hex = event.tags[0][1]
            if other_pubkey_hex.startswith("npub1"):
                _, data = decode_bech32(other_pubkey_hex)
                other_pubkey_hex = data.hex()
        else:
            other_pubkey_hex = event.pubkey
    else:
        # Active keypair is the RECIPIENT
        other_pubkey_hex = event.pubkey

    shared_secret = derive_shared_secret(active_keypair.private_key_hex, other_pubkey_hex)

    if "?iv=" not in event.content:
        raise ValueError("Invalid NIP-04 DM format (missing ?iv=)")

    payload_b64, iv_b64 = event.content.split("?iv=")
    data = base64.b64decode(payload_b64)
    nonce = base64.b64decode(iv_b64)

    ciphertext = data[:-16]
    auth_tag = data[-16:]

    plaintext = decrypt_payload(ciphertext, shared_secret, nonce, auth_tag)
    return plaintext.decode('utf-8')
