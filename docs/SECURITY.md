# Security Architecture & Threat Model

## 1. Cryptography Standards
- **Symmetric Encryption**: ChaCha20 + HMAC-SHA256 authenticated encryption (EtM) with 12-byte nonces.
- **Asymmetric Encryption**: ECDH shared key derivation over secp256k1 curve.
- **Signatures**: BIP-340 Schnorr signatures over SHA256 canonical event hashes.

## 2. Input Validation & Safety
- **Anti-Zip Bomb / Payload Limits**: Enforces strict size limits on decoded binary protocol buffers.
- **Replay Protection**: Nonce uniqueness verification and timestamp sliding window checks.
- **Untrusted Input Handling**: Carrier images are parsed safely using PIL without shell execution risks.
