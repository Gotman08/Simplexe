#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
PY="OR-Tools/.venv/bin/python3"

echo "=== Generation des visualisations TSP ==="
for f in graphe_12.txt graphe_13.txt graphe_14.txt graphe_15.txt \
         pd_5.tsp pd_11.tsp pd_15.tsp pd_18.tsp pd_22.tsp; do
    fichier="Fichiers tests - Voyageur de commerce-20260510/$f"
    if [[ -f "$fichier" ]]; then
        "$PY" -X utf8 OR-Tools/main.py --visualize tsp "$fichier"
    fi
done

echo
echo "=== Generation des visualisations Sac a Dos ==="
for f in prob_sac_1.txt prob_sac_3.txt prob_sac_5.txt prob_sac_10.txt \
         prob_sac_20.txt prob_sac_25.txt prob_sac_30.txt; do
    fichier="Fichiers tests - Sac à dos-20260510/$f"
    if [[ -f "$fichier" ]]; then
        "$PY" -X utf8 OR-Tools/main.py --visualize ukp "$fichier"
    fi
done

echo
echo "=== Inventaire final ==="
ls -la Resultats/visualisations/
ls -la Resultats/benchmarks/
