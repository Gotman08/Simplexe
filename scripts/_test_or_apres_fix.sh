#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
PY="OR-Tools/.venv/bin/python3"

echo "=== Verification OR-Tools sur prob_sac_20 (apres fix bornes) ==="
"$PY" OR-Tools/main.py --probleme ukp \
    --fichier "Fichiers tests - Sac à dos-20260510/prob_sac_20.txt" \
    --timeout 30
