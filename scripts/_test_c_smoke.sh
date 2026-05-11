#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

UKP_DIR="Fichiers tests - Sac à dos-20260510"
TSP_DIR="Fichiers tests - Voyageur de commerce-20260510"
BIN="Separation-Evaluation/bin/solveur"

echo "============================="
echo "  Tests UKP (TP3 references) "
echo "============================="
for f in prob_sac_1.txt prob_sac_2.txt prob_sac_3.txt prob_sac_4.txt prob_sac_5.txt; do
    echo "--- $f ---"
    "$BIN" --probleme ukp --fichier "$UKP_DIR/$f"
    echo
done

echo "================================"
echo "  Tests TSP (TP5 graphes)       "
echo "================================"
for f in graphe_12.txt graphe_13.txt graphe_14.txt graphe_15.txt; do
    echo "--- $f ---"
    "$BIN" --probleme tsp --fichier "$TSP_DIR/$f"
    echo
done

echo "================================"
echo "  Tests TSP (TSPLIB95 petits)   "
echo "================================"
for f in pd_5.tsp pd_11.tsp pd_15.tsp pd_18.tsp pd_22.tsp; do
    echo "--- $f ---"
    "$BIN" --probleme tsp --fichier "$TSP_DIR/$f"
    echo
done
