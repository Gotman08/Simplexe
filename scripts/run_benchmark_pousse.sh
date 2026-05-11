#!/usr/bin/env bash
# Lance le benchmark exhaustif local (équivalent du job Romeo).
#
# Usage :
#   bash scripts/run_benchmark_pousse.sh                    # instances obligatoires
#   bash scripts/run_benchmark_pousse.sh --inclure-grands   # + Partie 3 (jusqu'a 4h)
#   bash scripts/run_benchmark_pousse.sh --reps-petits 3 --reps-moyens 2

set -euo pipefail

cd "$(dirname "$0")/.."
RACINE="$(pwd)"

# Detecte le venv s'il existe, sinon utilise python3 directement
if [[ -x "OR-Tools/.venv/bin/python3" ]]; then
    PY="OR-Tools/.venv/bin/python3"
else
    PY="python3"
fi

INCLURE_GRANDS=0
REPS_PETITS=5
REPS_MOYENS=3
REPS_GRANDS=2

while [[ $# -gt 0 ]]; do
    case "$1" in
        --inclure-grands)  INCLURE_GRANDS=1; shift ;;
        --reps-petits)     REPS_PETITS="$2"; shift 2 ;;
        --reps-moyens)     REPS_MOYENS="$2"; shift 2 ;;
        --reps-grands)     REPS_GRANDS="$2"; shift 2 ;;
        -h|--help)
            echo "Options : --inclure-grands, --reps-petits N, --reps-moyens N, --reps-grands N"
            exit 0 ;;
        *)  echo "Option inconnue : $1"; exit 2 ;;
    esac
done

echo "============================================================"
echo "  Benchmark EXHAUSTIF (local) — equivalent Romeo"
echo "  Reps : petits=$REPS_PETITS, moyens=$REPS_MOYENS, grands=$REPS_GRANDS"
echo "  Inclure grands : $INCLURE_GRANDS"
echo "============================================================"

# 1. Compilation C (si necessaire)
if [[ ! -x "Separation-Evaluation/bin/solveur" ]]; then
    echo "[compile] Separation-Evaluation"
    (cd Separation-Evaluation && make)
fi

# 2. Lancement
ARGS=(--benchmark-pousse \
      --binaire-c "$RACINE/Separation-Evaluation/bin/solveur" \
      --reps-petits "$REPS_PETITS" \
      --reps-moyens "$REPS_MOYENS" \
      --reps-grands "$REPS_GRANDS")

if [[ "$INCLURE_GRANDS" -eq 1 ]]; then
    ARGS+=(--inclure-grands)
fi

"$PY" -X utf8 OR-Tools/main.py "${ARGS[@]}"
