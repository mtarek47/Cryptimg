#!/usr/bin/env bash
set -e

echo "🚀 Starting Stegstr API Server & Web Dashboard..."
echo "Web Interface: http://127.0.0.1:8765/app"
echo "OpenAPI Specs: http://127.0.0.1:8765/docs"

python3 -m stegstr.api.server
