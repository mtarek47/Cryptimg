#!/usr/bin/env bash
set -e

echo "=========================================="
echo "      Stegstr System Environment Setup     "
echo "=========================================="

chmod +x stegstr-cli
chmod +x scripts/*.sh 2>/dev/null || true

echo "✅ Made scripts executable."
echo "✅ Stegstr system environment ready."
