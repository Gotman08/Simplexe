#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
BIN="Separation-Evaluation/bin/solveur"
UKP_DIR="Fichiers tests - Sac à dos-20260510"

for f in prob_sac_10.txt prob_sac_20.txt prob_sac_25.txt prob_sac_30.txt; do
    echo "=== $f ==="
    timeout 90 "$BIN" --probleme ukp --fichier "$UKP_DIR/$f" --silent || echo "[timeout]"
done
