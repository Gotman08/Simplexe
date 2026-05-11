#!/usr/bin/env bash
# Phase 4 : TSP grands (pd_59, canada_4663, usa_13509)
# pd_59 : OR=60s, BB=30s
# canada_4663 : OR=90s, BB=30s
# usa_13509 : OR=180s, BB=15s
set -e
cd "$(dirname "$0")/.."
PY="OR-Tools/.venv/bin/python3"

"$PY" - <<'PY'
import sys
sys.path.insert(0, "OR-Tools")
from pathlib import Path
from src.benchmark_pousse import (
    ConfigBenchmarkPousse, _executer_runs, _ecrire_csv, _agreger,
    _charger_csv, auditer_qualite,
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

lignes_ukp = _charger_csv(cfg.dossier_resultats / "ukp_brut.csv")
lignes_tsp = _charger_csv(cfg.dossier_resultats / "tsp_brut.csv")

INSTANCES = [
    ("pd_59.tsp",         60.0, 30.0, 2),
    ("canada_4663.tsp",   90.0, 30.0, 2),
    ("usa_13509.tsp",    180.0, 15.0, 2),
]

for nom, t_or, t_bb, reps in INSTANCES:
    chemin = cfg.dossier_tests_tsp / nom
    print(f"\n--- {nom} (OR={t_or}s, BB={t_bb}s, {reps} reps) ---")
    nouvelles = _executer_runs(cfg, "tsp", chemin,
                                timeout_s=t_or, reps=reps, timeout_bb=t_bb)
    lignes_tsp.extend(nouvelles)

champs_brut = ["instance", "n", "methode", "rep", "valeur", "temps_s",
               "noeuds_generes", "memoire_kb", "statut", "timeout_s", "lp_racine"]
_ecrire_csv(cfg.dossier_resultats / "tsp_brut.csv", lignes_tsp, champs_brut)

champs_agg = ["instance", "methode", "n", "reps", "n_ok",
              "median", "min", "max", "stddev", "valeur_obj_median"]
_ecrire_csv(cfg.dossier_resultats / "tsp_agrege_temps.csv",
            _agreger(lignes_tsp, "temps_s"), champs_agg)

print("\nGénération des figures finales...")
tracer_panneau_principal(lignes_ukp, lignes_tsp,
                         cfg.dossier_resultats / "panneau_principal.png")
tracer_boxplot_temps(lignes_ukp, "UKP",
                     cfg.dossier_resultats / "boxplot_temps_ukp.png")
tracer_boxplot_temps(lignes_tsp, "TSP",
                     cfg.dossier_resultats / "boxplot_temps_tsp.png")
tracer_scaling_avec_erreurs(lignes_ukp, "UKP",
                             cfg.dossier_resultats / "scaling_ukp.png")
tracer_scaling_avec_erreurs(lignes_tsp, "TSP",
                             cfg.dossier_resultats / "scaling_tsp.png")
tracer_qualite_relative(lignes_ukp, lignes_tsp,
                        cfg.dossier_resultats / "qualite_relative.png")
tracer_performance_profile(lignes_ukp, lignes_tsp,
                            cfg.dossier_resultats / "performance_profile.png")

print("\n=== AUDIT QUALITE FINAL ===")
auditer_qualite(lignes_ukp, lignes_tsp, cfg.dossier_tests_ukp)
print("\nPhase 4 TERMINEE — BENCHMARK COMPLET")
PY
