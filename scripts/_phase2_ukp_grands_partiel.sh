#!/usr/bin/env bash
# Phase 2 partielle : seulement prob_sac_2000 (skip prob_sac_20000 trop volumineux)
set -e
cd "$(dirname "$0")/.."
PY="OR-Tools/.venv/bin/python3"

"$PY" - <<'PY'
import sys
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

racine = Path("/mnt/c/Users/nicol/Desktop/Simplexe").resolve()
cfg = ConfigBenchmarkPousse(
    racine=racine,
    binaire_c=racine / "Separation-Evaluation" / "bin" / "solveur",
    dossier_tests_ukp=racine / "Fichiers tests - Sac à dos-20260510",
    dossier_tests_tsp=racine / "Fichiers tests - Voyageur de commerce-20260510",
    dossier_resultats=racine / "Resultats" / "benchmarks_pousses",
    timeout_bb_grands=30.0,
    timeout_or_grands=60.0,
)
cfg.dossier_resultats.mkdir(parents=True, exist_ok=True)

lignes_ukp = _charger_csv(cfg.dossier_resultats / "ukp_brut.csv")
lignes_tsp = _charger_csv(cfg.dossier_resultats / "tsp_brut.csv")
deja = _instances_dejà(lignes_ukp + lignes_tsp)
print(f"Charge : {len(lignes_ukp)} lignes UKP, {len(lignes_tsp)} lignes TSP. Deja: {len(deja)}.")

cible = cfg.dossier_tests_ukp / "prob_sac_2000.txt"
inst_nom = cible.stem
if (inst_nom, "OR-Tools") in deja and (inst_nom, "B&B (C)") in deja:
    print("prob_sac_2000 deja fait, rien a faire.")
else:
    print(f"\n--- prob_sac_2000.txt (OR=60s, BB=30s, 2 reps) ---")
    nouvelles = _executer_runs(cfg, "ukp", cible, timeout_s=60.0, reps=2, timeout_bb=30.0)
    lignes_ukp.extend(nouvelles)

champs_brut = ["instance", "n", "methode", "rep", "valeur", "temps_s",
               "noeuds_generes", "memoire_kb", "statut", "timeout_s"]
_ecrire_csv(cfg.dossier_resultats / "ukp_brut.csv", lignes_ukp, champs_brut)

champs_agg = ["instance", "methode", "n", "reps", "n_ok",
              "median", "min", "max", "stddev", "valeur_obj_median"]
_ecrire_csv(cfg.dossier_resultats / "ukp_agrege_temps.csv",
            _agreger(lignes_ukp, "temps_s"), champs_agg)

print("\nFigures...")
tracer_panneau_principal(lignes_ukp, lignes_tsp,
                         cfg.dossier_resultats / "panneau_principal.png")
tracer_boxplot_temps(lignes_ukp, "UKP",
                     cfg.dossier_resultats / "boxplot_temps_ukp.png")
tracer_scaling_avec_erreurs(lignes_ukp, "UKP",
                             cfg.dossier_resultats / "scaling_ukp.png")
tracer_qualite_relative(lignes_ukp, lignes_tsp,
                        cfg.dossier_resultats / "qualite_relative.png")
print("Phase 2 partielle TERMINEE")
PY
