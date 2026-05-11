#!/usr/bin/env bash
# Phase 2 : UKP grands (prob_sac_2000 BB+OR / prob_sac_20000 OR seul)
set -e
cd "$(dirname "$0")/.."
PY="OR-Tools/.venv/bin/python3"

"$PY" - <<'PY'
import sys
sys.path.insert(0, "OR-Tools")
from pathlib import Path
from src.benchmark_pousse import (
    ConfigBenchmarkPousse, _executer_runs, _ecrire_csv, _agreger,
    _charger_csv, auditer_qualite, _resoudre_ukp_avec_memoire,
)
from src.parsers import lire_ukp
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

# prob_sac_2000 : BB+OR (timeout BB 30s, OR 60s, 2 reps)
print("\n--- prob_sac_2000.txt (BB=30s, OR=60s, 2 reps) ---")
chemin = cfg.dossier_tests_ukp / "prob_sac_2000.txt"
nouvelles = _executer_runs(cfg, "ukp", chemin, timeout_s=60.0, reps=2, timeout_bb=30.0)
lignes_ukp.extend(nouvelles)

# prob_sac_20000 : OR seul (BB skip délibéré)
print("\n--- prob_sac_20000.txt (OR seul, 2 reps) ---")
p = lire_ukp(cfg.dossier_tests_ukp / "prob_sac_20000.txt")
for r in range(1, 3):
    sol = _resoudre_ukp_avec_memoire(p, timeout_s=30.0)
    sol["methode"]   = "OR-Tools"
    sol["rep"]       = r
    sol["timeout_s"] = 30.0
    lignes_ukp.append(sol)
    lignes_ukp.append({
        "instance": p.nom, "n": p.n, "valeur": 0,
        "temps_s": 30.0, "noeuds_generes": 0, "memoire_kb": 0,
        "statut": "TIMEOUT_DELIBERE", "methode": "B&B (C)",
        "rep": r, "timeout_s": 30.0, "lp_racine": 0.0,
    })
    print(f"  [{r}/2] OR val={sol['valeur']} t={sol['temps_s']:.3f}s "
          f"BB skip délibéré")

champs_brut = ["instance", "n", "methode", "rep", "valeur", "temps_s",
               "noeuds_generes", "memoire_kb", "statut", "timeout_s", "lp_racine"]
_ecrire_csv(cfg.dossier_resultats / "ukp_brut.csv", lignes_ukp, champs_brut)

champs_agg = ["instance", "methode", "n", "reps", "n_ok",
              "median", "min", "max", "stddev", "valeur_obj_median"]
_ecrire_csv(cfg.dossier_resultats / "ukp_agrege_temps.csv",
            _agreger(lignes_ukp, "temps_s"), champs_agg)

print("\nFigures...")
tracer_panneau_principal(lignes_ukp, lignes_tsp,
                         cfg.dossier_resultats / "panneau_principal.png")
tracer_scaling_avec_erreurs(lignes_ukp, "UKP",
                             cfg.dossier_resultats / "scaling_ukp.png")
tracer_boxplot_temps(lignes_ukp, "UKP",
                     cfg.dossier_resultats / "boxplot_temps_ukp.png")
tracer_qualite_relative(lignes_ukp, lignes_tsp,
                        cfg.dossier_resultats / "qualite_relative.png")
tracer_performance_profile(lignes_ukp, lignes_tsp,
                            cfg.dossier_resultats / "performance_profile.png")
print("Phase 2 TERMINEE")
PY
