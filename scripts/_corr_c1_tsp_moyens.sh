#!/usr/bin/env bash
# C-1 : retire les lignes BB pd_18/pd_20/pd_22 du CSV brut, relance avec timeout 90s,
#       puis ré-agrège et régénère toutes les figures.
set -e
cd "$(dirname "$0")/.."
PY="OR-Tools/.venv/bin/python3"

"$PY" - <<'PY'
import sys
sys.path.insert(0, "OR-Tools")
from pathlib import Path
from src.benchmark_pousse import (
    ConfigBenchmarkPousse, _executer_runs, _ecrire_csv, _agreger,
    _charger_csv,
)
from src.visualization_pousse import (
    tracer_panneau_principal, tracer_boxplot_temps,
    tracer_scaling_avec_erreurs, tracer_qualite_relative,
)

racine = Path("/mnt/c/Users/nicol/Desktop/Simplexe").resolve()
cfg = ConfigBenchmarkPousse(
    racine=racine,
    binaire_c=racine / "Separation-Evaluation" / "bin" / "solveur",
    dossier_tests_ukp=racine / "Fichiers tests - Sac à dos-20260510",
    dossier_tests_tsp=racine / "Fichiers tests - Voyageur de commerce-20260510",
    dossier_resultats=racine / "Resultats" / "benchmarks_pousses",
)

lignes_ukp = _charger_csv(cfg.dossier_resultats / "ukp_brut.csv")
lignes_tsp = _charger_csv(cfg.dossier_resultats / "tsp_brut.csv")

A_RETIRER = {"pd_18", "pd_20", "pd_22"}
avant = len(lignes_tsp)
lignes_tsp = [
    l for l in lignes_tsp
    if not (l["instance"] in A_RETIRER and l["methode"] == "B&B (C)")
]
print(f"Retire {avant - len(lignes_tsp)} lignes BB obsoletes pour pd_18/20/22.")

# Relance BB UNIQUEMENT (3 reps, timeout 90s)
from src.benchmark_pousse import _executer_c
import subprocess

for nom in ["pd_18.tsp", "pd_20.tsp", "pd_22.tsp"]:
    chemin = cfg.dossier_tests_tsp / nom
    print(f"\n--- {nom} (BB seul, timeout 90s, 3 reps) ---")
    for r in range(1, 4):
        result = _executer_c(cfg.binaire_c, "tsp", chemin, 90.0)
        if result is None:
            print(f"  [{r}/3] BB introuvable")
            continue
        if result.get("timeout"):
            ligne = {
                "instance": chemin.stem,
                "n": 0,
                "methode": "B&B (C)",
                "rep": r,
                "valeur": 0,
                "temps_s": 90.0,
                "noeuds_generes": 0,
                "memoire_kb": 0,
                "statut": "TIMEOUT",
                "timeout_s": 90.0,
            }
            print(f"  [{r}/3] TIMEOUT (90s)")
        else:
            ligne = {
                "instance": result["instance"],
                "n": 0,
                "methode": "B&B (C)",
                "rep": r,
                "valeur": result["valeur"],
                "temps_s": result["temps_s"],
                "noeuds_generes": result["noeuds_generes"],
                "memoire_kb": 0,
                "statut": "OK",
                "timeout_s": 90.0,
            }
            print(f"  [{r}/3] val={result['valeur']:<8} t={result['temps_s']:.3f}s OK")
        # Recuperer n depuis le CSV existant
        for autre in lignes_tsp:
            if autre["instance"] == chemin.stem and autre.get("n"):
                ligne["n"] = autre["n"]
                break
        lignes_tsp.append(ligne)

champs_brut = ["instance", "n", "methode", "rep", "valeur", "temps_s",
               "noeuds_generes", "memoire_kb", "statut", "timeout_s"]
_ecrire_csv(cfg.dossier_resultats / "tsp_brut.csv", lignes_tsp, champs_brut)

champs_agg = ["instance", "methode", "n", "reps", "n_ok",
              "median", "min", "max", "stddev", "valeur_obj_median"]
_ecrire_csv(cfg.dossier_resultats / "tsp_agrege_temps.csv",
            _agreger(lignes_tsp, "temps_s"), champs_agg)

print("\nRégénération des figures...")
tracer_panneau_principal(lignes_ukp, lignes_tsp,
                         cfg.dossier_resultats / "panneau_principal.png")
tracer_boxplot_temps(lignes_tsp, "TSP",
                     cfg.dossier_resultats / "boxplot_temps_tsp.png")
tracer_scaling_avec_erreurs(lignes_tsp, "TSP",
                             cfg.dossier_resultats / "scaling_tsp.png")
tracer_qualite_relative(lignes_ukp, lignes_tsp,
                        cfg.dossier_resultats / "qualite_relative.png")
print("C-1 TERMINEE")
PY
