#!/usr/bin/env bash
# Phase 3 : TSP petits (5 reps) + TSP moyens (3 reps) avec BB timeout adapté.
# tsp_petits : OR=5s, BB=10s
# tsp_moyens : OR=15s, BB=90s (pour permettre la convergence pd_20/pd_22)
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
    tracer_performance_profile,
)

racine = Path("/mnt/c/Users/nicol/Desktop/Simplexe").resolve()
cfg = ConfigBenchmarkPousse(
    racine=racine,
    binaire_c=racine / "Separation-Evaluation" / "bin" / "solveur",
    dossier_tests_ukp=racine / "Fichiers tests - Sac à dos-20260510",
    dossier_tests_tsp=racine / "Fichiers tests - Voyageur de commerce-20260510",
    dossier_resultats=racine / "Resultats" / "benchmarks_pousses",
)
cfg.dossier_resultats.mkdir(parents=True, exist_ok=True)

lignes_ukp = _charger_csv(cfg.dossier_resultats / "ukp_brut.csv")
lignes_tsp = _charger_csv(cfg.dossier_resultats / "tsp_brut.csv")

# tsp_petits : OR=5s, BB=10s, 5 reps
TSP_PETITS = ["graphe_12.txt", "graphe_13.txt", "graphe_14.txt", "graphe_15.txt",
              "pd_5.tsp", "pd_11.tsp", "pd_15.tsp"]
print("=== tsp_petits (OR=5s, BB=10s, 5 reps) ===")
for nom in TSP_PETITS:
    chemin = cfg.dossier_tests_tsp / nom
    print(f"\n--- {nom} ---")
    nouvelles = _executer_runs(cfg, "tsp", chemin, timeout_s=5.0, reps=5, timeout_bb=10.0)
    lignes_tsp.extend(nouvelles)

# tsp_moyens : OR=15s, BB=90s, 3 reps
TSP_MOYENS = ["pd_18.tsp", "pd_20.tsp", "pd_22.tsp"]
print("\n=== tsp_moyens (OR=15s, BB=90s, 3 reps) ===")
for nom in TSP_MOYENS:
    chemin = cfg.dossier_tests_tsp / nom
    print(f"\n--- {nom} ---")
    nouvelles = _executer_runs(cfg, "tsp", chemin, timeout_s=15.0, reps=3, timeout_bb=90.0)
    lignes_tsp.extend(nouvelles)

champs_brut = ["instance", "n", "methode", "rep", "valeur", "temps_s",
               "noeuds_generes", "memoire_kb", "statut", "timeout_s", "lp_racine"]
_ecrire_csv(cfg.dossier_resultats / "tsp_brut.csv", lignes_tsp, champs_brut)

champs_agg = ["instance", "methode", "n", "reps", "n_ok",
              "median", "min", "max", "stddev", "valeur_obj_median"]
_ecrire_csv(cfg.dossier_resultats / "tsp_agrege_temps.csv",
            _agreger(lignes_tsp, "temps_s"), champs_agg)

print("\nFigures...")
tracer_panneau_principal(lignes_ukp, lignes_tsp,
                         cfg.dossier_resultats / "panneau_principal.png")
tracer_boxplot_temps(lignes_tsp, "TSP",
                     cfg.dossier_resultats / "boxplot_temps_tsp.png")
tracer_scaling_avec_erreurs(lignes_tsp, "TSP",
                             cfg.dossier_resultats / "scaling_tsp.png")
tracer_qualite_relative(lignes_ukp, lignes_tsp,
                        cfg.dossier_resultats / "qualite_relative.png")
tracer_performance_profile(lignes_ukp, lignes_tsp,
                            cfg.dossier_resultats / "performance_profile.png")
print("Phase 3 TERMINEE")
PY
