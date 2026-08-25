# Stegstr Technical Architecture

Stegstr is designed as a decoupled, modular system separating core cryptographic/steganographic operations from network synchronization and presentation interfaces.

```
+-----------------------------------------------------------------------+
|                           User / AI Agent                             |
|          (Web Dashboard / CLI `stegstr-cli` / REST API)               |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                           StegEngine                                  |
|  - Carrier Quality Analyzer (PSNR / SSIM / Texture score)             |
|  - Auto Codec Selector (Robust DCT QIM vs Legacy PNG LSB)             |
|  - Forward Error Correction (Reed-Solomon FEC & Byte Interleaving)    |
|  - Multi-Carrier Payload Fragmentation & Reassembly                   |
+-----------------------------------------------------------------------+
                   |                               |
                   v                               v
+-------------------------------+ +-------------------------------------+
|        Stego Codecs           | |            Binary Protocol          |
|  - Robust 2D-DCT QIM Codec    | |  - 121B Header (STG2 Magic)         |
|  - Legacy PNG LSB Codec       | |  - Zlib Dynamic Compression         |
|  - Sync Marker Alignment      | |  - CRC32 Checksum Integrity          |
+-------------------------------+ +-------------------------------------+
                                                   |
                                                   v
+-----------------------------------------------------------------------+
|                       Nostr & Cryptography Layer                      |
|  - secp256k1 Keys & Bech32 (npub/nsec)                                |
|  - BIP-340 Schnorr Signatures & NIP-01 Event Verification             |
|  - NIP-04 / NIP-44 Encrypted Direct Messages (ChaCha20 + HMAC)       |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                    Networking & Local Storage Layer                   |
|  - Multi-Relay WebSocket Connection Pool & Latency Health Monitor     |
|  - Offline Message Queue & Reconnection Synchronization Engine        |
|  - SQLite Local Database (`stegstr.db`)                               |
+-----------------------------------------------------------------------+
```
