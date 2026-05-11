#!/usr/bin/env bash
# Regenere les figures principales depuis ukp_brut.csv et tsp_brut.csv
# (n'oblige pas a relancer tout le benchmark exhaustif).
# Cible : panneau_principal.png, boxplot_temps_{ukp,tsp}.png
set -e
cd "$(dirname "$0")/.."

PY="${PY:-python3}"

"$PY" - <<'PY'
import sys, csv
sys.path.insert(0, "OR-Tools")
from pathlib import Path
from src.visualization_pousse import (
    tracer_panneau_principal,
    tracer_boxplot_temps,
)


def lire_csv(chemin):
    lignes = []
    with open(chemin, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                row["n"] = int(row["n"])
            except (TypeError, ValueError):
                continue
            for cle in ("valeur", "noeuds_generes", "memoire_kb"):
                if cle in row:
                    try:
                        row[cle] = int(row[cle])
                    except (TypeError, ValueError):
                        row[cle] = 0
            for cle in ("temps_s", "timeout_s"):
                if cle in row:
                    try:
                        row[cle] = float(row[cle])
                    except (TypeError, ValueError):
                        row[cle] = 0.0
            lignes.append(row)
    return lignes


dossier = Path("Resultats/benchmarks_pousses")
lignes_ukp = lire_csv(dossier / "ukp_brut.csv")
lignes_tsp = lire_csv(dossier / "tsp_brut.csv")
print(f"UKP : {len(lignes_ukp)} lignes ; TSP : {len(lignes_tsp)} lignes")

cible = dossier / "panneau_principal.png"
tracer_panneau_principal(lignes_ukp, lignes_tsp, cible)
print(f"-> {cible}")

cible_ukp = dossier / "boxplot_temps_ukp.png"
tracer_boxplot_temps(lignes_ukp, "UKP", cible_ukp)
print(f"-> {cible_ukp}")

cible_tsp = dossier / "boxplot_temps_tsp.png"
tracer_boxplot_temps(lignes_tsp, "TSP", cible_tsp)
print(f"-> {cible_tsp}")
PY
