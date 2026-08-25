# Stegstr Installation Guide

## Requirements
- macOS, Linux, or Windows
- Python 3.11+
- Standard Python libraries (`numpy`, `pillow`, `ecdsa`, `fastapi`, `uvicorn`, `pydantic`, `sqlite3`)

## Standard Installation

```bash
git clone https://github.com/stegstr/stegstr.git
cd stegstr
./scripts/setup.sh
```

## Running the Application

- **CLI Usage**: `./stegstr-cli --help`
- **Web Interface**: `./scripts/dev.sh` -> open `http://127.0.0.1:8765/app`
- **Run Tests**: `./scripts/test.sh`
- **Run Benchmark**: `./scripts/benchmark.sh sample_carrier.jpg`
