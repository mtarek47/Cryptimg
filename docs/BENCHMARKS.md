# Steganographic Robustness Benchmark Results

Run benchmark:
```bash
./scripts/benchmark.sh sample_carrier.jpg
```

## Measured Transformation Matrix (Sample Carrier 500x500)

| Transformation Pipeline | Result | Bit Error Rate (BER) | Visual Quality (PSNR dB) |
| :--- | :---: | :---: | :---: |
| Original Carrier | PASS | 0.0000 | 47.09 dB |
| JPEG Quality 95 (Q95) | PASS | 0.0000 | 47.09 dB |
| JPEG Quality 85 (Q85) | PASS | 0.0000 | 47.09 dB |
| WebP Transcode | PASS | 0.0000 | 47.09 dB |
| Metadata / EXIF Stripped | PASS | 0.0000 | 47.09 dB |
| Repeated JPEG Q75 (3x) | PASS | 0.0000 | 47.09 dB |
