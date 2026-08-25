#!/usr/bin/env bash
set -e

CARRIER=${1:-"sample_carrier.jpg"}

echo "=========================================="
echo "   Stegstr Media Transformation Benchmark "
echo "=========================================="

python3 -c "
from benchmarks.benchmark_suite import run_robustness_benchmark
import json

res = run_robustness_benchmark('$CARRIER')
print(json.dumps(res, indent=2))
"
