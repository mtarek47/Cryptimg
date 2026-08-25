#!/usr/bin/env bash
set -e

echo "=========================================="
echo "      Running Stegstr Test Suite          "
echo "=========================================="

python3 -m unittest discover -s stegstr/tests -p "test_*.py"
