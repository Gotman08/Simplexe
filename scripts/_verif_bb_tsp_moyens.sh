#!/usr/bin/env bash
# Test BB sur pd_18, pd_20, pd_22 avec timeout suffisant pour observer la convergence
set -e
cd "$(dirname "$0")/.."
BIN="Separation-Evaluation/bin/solveur"

for f in pd_18.tsp pd_20.tsp pd_22.tsp; do
    echo "=== $f (timeout 90s) ==="
    timeout 90 "$BIN" --probleme tsp \
        --fichier "Fichiers tests - Voyageur de commerce-20260510/$f" \
        --silent || echo "[depasse 90s]"
done
