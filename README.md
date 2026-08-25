# Stegstr — Production-Grade Steganographic Nostr Client & Engine

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![Nostr Protocol](https://img.shields.io/badge/nostr-NIP--01%20%7C%20NIP--04-purple.svg)](https://nostr.com)

**Stegstr** is a production-quality, transformation-resistant steganographic social networking client and payload transport engine built for the Nostr ecosystem.

Unlike traditional steganography tools that rely on fragile spatial PNG LSB embedding (which collapses under lossy compression), Stegstr introduces a **Mid-Frequency 2D-DCT Quantization Index Modulation (QIM)** engine coupled with **Reed-Solomon Forward Error Correction (FEC)** operating on luminance block frequencies. Stegstr hidden payloads survive real-world social media media pipelines: lossy JPEG re-encoding (down to Q45), WebP format conversion, resolution scaling, metadata/EXIF stripping, and repeated recompression.

---

## Key Architectural Features

- **Transformation-Resistant StegEngine**: Mid-frequency 2D-DCT block QIM steganography surviving lossy JPEG/WebP pipelines.
- **Legacy Compatibility Mode**: 100% backward compatible with original Stegstr PNG LSB payloads.
- **Reed-Solomon Forward Error Correction**: Adjustable parity redundancy (Fast, Balanced, Robust, Maximum) with byte interleaving.
- **Compact Binary Protocol**: 121-byte compact header with zlib compression, message UUIDs, timestamps, and CRC32 integrity validation.
- **Nostr Cryptography & Protocol**: BIP-340 Schnorr signatures, secp256k1 keypairs, NIP-01 events, `npub`/`nsec` Bech32 encoding, and NIP-04/NIP-44 encrypted DMs.
- **Multi-Relay Pool & Offline Queue**: Asynchronous WebSocket relay connection pool with latency health tracking, auto-reconnect backoff, and offline event queueing.
- **AI Agent Operability**: Full headless CLI (`stegstr-cli`) with `--json` machine-readable output, REST API, OpenAPI docs, `agents.txt`, and `AGENTS.md`.
- **Automated Transformation Test Harness**: Automated benchmark suite evaluating JPEG Q95-Q45, WebP, resizing, metadata stripping, and repeated recompression with PSNR/SSIM metrics.
- **Modern Web Dashboard UI**: Responsive dark-mode dashboard for timeline feeds, encrypted messaging, drag-and-drop embedding, detection scanning, and diagnostics.

---

## Quick Start (One-Command Setup)

### 1. Setup & Dependencies
```bash
./scripts/setup.sh
```

### 2. Run Test Suite
```bash
./scripts/test.sh
```

### 3. Run Steganographic Robustness Benchmark
```bash
./scripts/benchmark.sh sample_carrier.jpg
```

### 4. Launch Local API Server & Web UI Dashboard
```bash
./scripts/dev.sh
```
Access the dashboard at: `http://127.0.0.1:8765/app`
OpenAPI Swagger docs at: `http://127.0.0.1:8765/docs`

---

## Headless CLI Usage (`stegstr-cli`)

```bash
# Embed message into cover image
./stegstr-cli encode cover.jpg -m "Secret Nostr Message" -o stego.jpg --robustness balanced --json

# Extract payload from carrier image
./stegstr-cli decode stego.jpg --json

# Scan image or directory for Stegstr payloads
./stegstr-cli detect ./images/ --json

# Create Nostr post
./stegstr-cli post "Hello Stegstr" -c cover.jpg --json

# Inspect carrier capacity & texture score
./stegstr-cli inspect carrier.jpg --json

# Test Nostr relay pool
./stegstr-cli relay test --json
```

---

## Documentation

Detailed documentation is available in the `docs/` directory:
- [`ARCHITECTURE.md`](docs/ARCHITECTURE.md): System architecture and component breakdown
- [`STEGO.md`](docs/STEGO.md): Steganography algorithms, DCT QIM mathematics, and FEC design
- [`NOSTR.md`](docs/NOSTR.md): Nostr protocol implementation, key derivation, and event signing
- [`NETWORKING.md`](docs/NETWORKING.md): Relay management, offline queue, and sync engine
- [`SECURITY.md`](docs/SECURITY.md): Threat model, cryptography, anti-tamper, and safety
- [`AI_AGENTS.md`](AGENTS.md): Integration guide for AI agents and LLM tool automation
- [`TESTING.md`](docs/TESTING.md): Test harness and verification guidelines
- [`BENCHMARKS.md`](docs/BENCHMARKS.md): Measured robustness and perceptual visual quality results

---

## License

MIT License. Free and open-source software.
