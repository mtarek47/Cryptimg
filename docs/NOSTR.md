# Nostr Protocol Integration

## 1. NIP-01 Event Format & Canonical Serialization
Events follow standard Nostr NIP-01 specifications:
```json
{
  "id": "4376c65d2f219119...",
  "pubkey": "d9812a...",
  "created_at": 1787037762,
  "kind": 1,
  "tags": [],
  "content": "Hello Stegstr",
  "sig": "9821af..."
}
```

Canonical serialization for SHA256 hashing:
`[0, pubkey, created_at, kind, tags, content]`

## 2. BIP-340 Schnorr Signatures
- **secp256k1 Curve**: Keypairs derive x-only 32-byte public keys.
- **Even Y-coordinate Rule**: Enforces $P.y \bmod 2 == 0$, negating secret exponent if Y is odd.
- **Bech32 Encoding**: Supports standard `npub1...` and `nsec1...` strings.
