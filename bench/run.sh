#!/usr/bin/env bash
# Correctness evidence only; this does not invoke the historical benchmark suite.
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
PYTHON=${PYTHON:-python3}
OUTPUT=${1:-bench/results/local}
mkdir -p "$OUTPUT"
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
{
    date -u --iso-8601=seconds
    uname -srm
    cat /etc/os-release
    gcc --version
    cc --version
    make --version
    dpkg-query -W libglpk-dev libglpk40
    make --no-print-directory -C Separation-Evaluation -B -j2
    timeout 90 make --no-print-directory -C Separation-Evaluation run-test
} 2>&1 | tee "$OUTPUT/build.log"
"$PYTHON" -m pip freeze > "$OUTPUT/requirements.txt"
"$PYTHON" -u tests/verify.py --output "$OUTPUT" 2>&1 | tee "$OUTPUT/verification.log"
{
    "$PYTHON" OR-Tools/main.py --help
    "$PYTHON" OR-Tools/main.py --probleme ukp \
        --fichier 'Fichiers tests - Sac à dos-20260510/prob_sac_1.txt' \
        --timeout 1 --export "$OUTPUT/solutions"
    "$PYTHON" OR-Tools/main.py --probleme tsp \
        --fichier 'Fichiers tests - Voyageur de commerce-20260510/pd_5.tsp' \
        --timeout 1 --export "$OUTPUT/solutions"
} 2>&1 | tee "$OUTPUT/cli.log"
