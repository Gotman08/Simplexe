#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
BIN="Separation-Evaluation/bin/solveur"
TSP_DIR="Fichiers tests - Voyageur de commerce-20260510"

for f in graphe_12.txt graphe_13.txt graphe_14.txt graphe_15.txt pd_5.tsp pd_11.tsp pd_15.tsp pd_18.tsp pd_22.tsp; do
    echo "=== $f ==="
    timeout 60 "$BIN" --probleme tsp --fichier "$TSP_DIR/$f" --silent || echo "[timeout]"
done
