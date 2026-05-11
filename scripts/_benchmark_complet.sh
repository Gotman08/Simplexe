#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
PY="OR-Tools/.venv/bin/python3"

echo "=== Benchmark complet : BB(C) vs OR-Tools(Python) ==="
"$PY" -X utf8 OR-Tools/main.py --benchmark --timeout 30 \
    --binaire-c "$(pwd)/Separation-Evaluation/bin/solveur"
