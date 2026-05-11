#!/usr/bin/env bash
# Phase 2 isolee : prob_sac_20000 seulement
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
    timeout_or_grands=30.0,
)
cfg.dossier_resultats.mkdir(parents=True, exist_ok=True)

lignes_ukp = _charger_csv(cfg.dossier_resultats / "ukp_brut.csv")
lignes_tsp = _charger_csv(cfg.dossier_resultats / "tsp_brut.csv")
deja = _instances_dejà(lignes_ukp + lignes_tsp)

cible = cfg.dossier_tests_ukp / "prob_sac_20000.txt"
inst_nom = cible.stem
print(f"Test {inst_nom} : OR seulement (2 reps), BB skip (timeout systematique)")

# Lancement OR-Tools seul (pas le BB qui ne converge jamais)
from src.parsers import lire_ukp
from src.benchmark_pousse import _resoudre_ukp_avec_memoire
probleme = lire_ukp(cible)
print(f"  parsed n={probleme.n}, capacite={probleme.capacite}")
for r in range(1, 3):
    ligne_or = _resoudre_ukp_avec_memoire(probleme, timeout_s=30.0)
    ligne_or["methode"]   = "OR-Tools"
    ligne_or["rep"]       = r
    ligne_or["timeout_s"] = 30.0
    lignes_ukp.append(ligne_or)
    print(f"  [{r}/2] OR-Tools val={ligne_or['valeur']} t={ligne_or['temps_s']:.3f}s ({ligne_or['statut']})")
    # BB explicit timeout
    ligne_bb = {
        "instance": probleme.nom,
        "n": probleme.n,
        "valeur": 0,
        "temps_s": 30.0,
        "noeuds_generes": 0,
        "memoire_kb": 0,
        "statut": "TIMEOUT_DELIBERE",
        "methode": "B&B (C)",
        "rep": r,
        "timeout_s": 30.0,
    }
    lignes_ukp.append(ligne_bb)
    print(f"  [{r}/2] B&B    skip (BB ne converge pas pour n=20000, marque TIMEOUT_DELIBERE)")

champs_brut = ["instance", "n", "methode", "rep", "valeur", "temps_s",
               "noeuds_generes", "memoire_kb", "statut", "timeout_s"]
_ecrire_csv(cfg.dossier_resultats / "ukp_brut.csv", lignes_ukp, champs_brut)

champs_agg = ["instance", "methode", "n", "reps", "n_ok",
              "median", "min", "max", "stddev", "valeur_obj_median"]
_ecrire_csv(cfg.dossier_resultats / "ukp_agrege_temps.csv",
            _agreger(lignes_ukp, "temps_s"), champs_agg)

print("Figures...")
tracer_panneau_principal(lignes_ukp, lignes_tsp,
                         cfg.dossier_resultats / "panneau_principal.png")
tracer_boxplot_temps(lignes_ukp, "UKP",
                     cfg.dossier_resultats / "boxplot_temps_ukp.png")
tracer_scaling_avec_erreurs(lignes_ukp, "UKP",
                             cfg.dossier_resultats / "scaling_ukp.png")
tracer_qualite_relative(lignes_ukp, lignes_tsp,
                        cfg.dossier_resultats / "qualite_relative.png")
print("Phase 2 / 20000 TERMINEE")
PY
