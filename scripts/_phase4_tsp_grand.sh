#!/usr/bin/env bash
# Phase 4 modulaire : une instance TSP grande a la fois.
# Usage : bash _phase4_tsp_grand.sh <fichier_tsp> [reps] [timeout_or] [timeout_bb]

set -e
cd "$(dirname "$0")/.."
PY="OR-Tools/.venv/bin/python3"

INSTANCE="${1:-pd_59.tsp}"
REPS="${2:-2}"
TIMEOUT_OR="${3:-90}"
TIMEOUT_BB="${4:-30}"

INSTANCE_NAME="$INSTANCE" REPS="$REPS" TIMEOUT_OR="$TIMEOUT_OR" TIMEOUT_BB="$TIMEOUT_BB" \
"$PY" - <<'PY'
import os, sys
sys.path.insert(0, "OR-Tools")
from pathlib import Path
from src.benchmark_pousse import (
    ConfigBenchmarkPousse, _executer_runs, _ecrire_csv, _agreger,
    _charger_csv, _instances_dejà,
)
from src.visualization_pousse import (
    tracer_panneau_principal, tracer_boxplot_temps,
    tracer_scaling_avec_erreurs, tracer_qualite_relative,
)

instance_name = os.environ["INSTANCE_NAME"]
reps          = int(os.environ["REPS"])
timeout_or    = float(os.environ["TIMEOUT_OR"])
timeout_bb    = float(os.environ["TIMEOUT_BB"])

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

cible = cfg.dossier_tests_tsp / instance_name
print(f"Test {instance_name} : OR={timeout_or}s, BB={timeout_bb}s, reps={reps}")
nouvelles = _executer_runs(cfg, "tsp", cible, timeout_s=timeout_or, reps=reps, timeout_bb=timeout_bb)
lignes_tsp.extend(nouvelles)

champs_brut = ["instance", "n", "methode", "rep", "valeur", "temps_s",
               "noeuds_generes", "memoire_kb", "statut", "timeout_s"]
_ecrire_csv(cfg.dossier_resultats / "ukp_brut.csv", lignes_ukp, champs_brut)
_ecrire_csv(cfg.dossier_resultats / "tsp_brut.csv", lignes_tsp, champs_brut)

champs_agg = ["instance", "methode", "n", "reps", "n_ok",
              "median", "min", "max", "stddev", "valeur_obj_median"]
_ecrire_csv(cfg.dossier_resultats / "tsp_agrege_temps.csv",
            _agreger(lignes_tsp, "temps_s"), champs_agg)

print("Figures...")
tracer_panneau_principal(lignes_ukp, lignes_tsp,
                         cfg.dossier_resultats / "panneau_principal.png")
tracer_boxplot_temps(lignes_tsp, "TSP",
                     cfg.dossier_resultats / "boxplot_temps_tsp.png")
tracer_scaling_avec_erreurs(lignes_tsp, "TSP",
                             cfg.dossier_resultats / "scaling_tsp.png")
tracer_qualite_relative(lignes_ukp, lignes_tsp,
                        cfg.dossier_resultats / "qualite_relative.png")
print(f"{instance_name} : TERMINEE")
PY
