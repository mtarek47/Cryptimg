# Testing Suite & Verification

Execute the complete automated test suite:
```bash
./scripts/test.sh
```

## Test Coverage
- `test_crypto.py`: ChaCha20 + HMAC-SHA256 authenticated encryption, nonces, key derivation.
- `test_fec.py`: Reed-Solomon error correction and matrix bit interleaving.
- `test_binary_protocol.py`: Compact binary protocol packing, CRC32, zlib compression.
- `test_nostr.py`: Secp256k1 key generation, BIP-340 Schnorr signing, verification.
- `test_stego_robustness.py`: Robust DCT QIM steganography encode/decode, PSNR, SSIM.
- `test_media_transformations.py`: Survival under JPEG Q95, Q85, metadata stripping, 3x repeated recompression.
- `test_fuzzing.py`: Random noise and corrupted image safety tests.
