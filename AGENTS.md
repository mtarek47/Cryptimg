# AI Agent Integration Guide — Stegstr

Stegstr provides first-class support for autonomous AI agents and automated scripts via a headless CLI (`stegstr-cli`) with `--json` output, a local REST API (`http://127.0.0.1:8765`), and OpenAPI documentation (`http://127.0.0.1:8765/docs`).

---

## 1. Machine-Readable CLI Interface

All `stegstr-cli` commands support the `--json` flag, returning structured JSON payloads for AI parsing.

### Encode Payload
```bash
./stegstr-cli encode carrier.jpg -m "Secret Nostr Message" -o stego_out.jpg --robustness balanced --json
```
**JSON Response**:
```json
{
  "status": "SUCCESS",
  "codec": "Robust Mid-Frequency 2D-DCT QIM Codec",
  "mode": "auto",
  "robustness": "balanced",
  "payload_size_bytes": 142,
  "total_stream_bytes": 280,
  "psnr_db": 44.82,
  "ssim": 0.9856,
  "output_path": "stego_out.jpg"
}
```

### Decode Carrier
```bash
./stegstr-cli decode stego_out.jpg --json
```
**JSON Response**:
```json
{
  "status": "FOUND",
  "codec": "Robust Mid-Frequency 2D-DCT QIM Codec",
  "source": "stego_out.jpg",
  "message": "Secret Nostr Message",
  "sender": "d9812a...",
  "valid_signature": true
}
```

### Batch Detect
```bash
./stegstr-cli detect ./images/ --json
```

### Robustness Benchmark
```bash
./stegstr-cli benchmark sample.jpg --json
```

---

## 2. Local REST API Endpoints

- `GET /api/v1/status`: System status and active Nostr identity.
- `POST /api/v1/encode`: Form-data image upload + message.
- `POST /api/v1/decode`: Form-data image upload payload extraction.
- `POST /api/v1/detect`: Detection scanner endpoint.
- `GET /api/v1/relays`: List relay health states.
- `GET /docs`: Interactive OpenAPI Swagger UI.
