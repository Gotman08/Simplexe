#!/usr/bin/env bash
# Pipeline complet : compile la partie C, installe les dépendances Python,
# lance le benchmark croisé et génère toutes les visualisations clés.
#
# Usage :
#   bash scripts/run_all.sh                  # batterie obligatoire (Parties 1 & 2)
#   bash scripts/run_all.sh --grands         # ajoute les très grandes instances
#   bash scripts/run_all.sh --pas-de-c       # saute la compilation C
#   bash scripts/run_all.sh --pas-de-pip     # saute pip install

set -euo pipefail

cd "$(dirname "$0")/.."
RACINE="$(pwd)"

INCLURE_GRANDS=0
COMPILER_C=1
INSTALLER_PY=1
TIMEOUT=20

for arg in "$@"; do
    case "$arg" in
        --grands)      INCLURE_GRANDS=1 ;;
        --pas-de-c)    COMPILER_C=0 ;;
        --pas-de-pip)  INSTALLER_PY=0 ;;
        --timeout=*)   TIMEOUT="${arg#--timeout=}" ;;
        -h|--help)
            grep -E '^# ' "$0" | sed 's/^# //'
            exit 0
            ;;
    esac
done

if [[ "$COMPILER_C" -eq 1 ]]; then
    echo "=== [1/3] Compilation Separation-Evaluation ==="
    (cd "$RACINE/Separation-Evaluation" && make)
fi

if [[ "$INSTALLER_PY" -eq 1 ]]; then
    echo "=== [2/3] Installation des dependances Python ==="
    pip install -r "$RACINE/OR-Tools/requirements.txt"
fi

echo "=== [3/3] Benchmark croisé ==="
ARGS=("--benchmark" "--timeout" "$TIMEOUT")
if [[ "$INCLURE_GRANDS" -eq 1 ]]; then
    ARGS+=("--inclure-grands")
fi
python3 "$RACINE/OR-Tools/main.py" "${ARGS[@]}"

echo
echo "=== Visualisations clés ==="
mkdir -p "$RACINE/Resultats/visualisations"

INSTANCES_TSP=(
    "graphe_12.txt"
    "pd_5.tsp"
    "pd_15.tsp"
    "pd_22.tsp"
)
for inst in "${INSTANCES_TSP[@]}"; do
    fichier="$RACINE/Fichiers tests - Voyageur de commerce-20260510/$inst"
    [[ -f "$fichier" ]] && python3 "$RACINE/OR-Tools/main.py" --visualize tsp "$fichier"
done

INSTANCES_UKP=(
    "prob_sac_1.txt"
    "prob_sac_5.txt"
    "prob_sac_20.txt"
    "prob_sac_30.txt"
)
for inst in "${INSTANCES_UKP[@]}"; do
    fichier="$RACINE/Fichiers tests - Sac à dos-20260510/$inst"
    [[ -f "$fichier" ]] && python3 "$RACINE/OR-Tools/main.py" --visualize ukp "$fichier"
done

echo
echo "Terminé. Résultats dans : $RACINE/Resultats/"
