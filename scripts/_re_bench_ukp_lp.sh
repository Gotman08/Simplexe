#!/usr/bin/env bash
# Relance UKP petits + moyens pour capter le nouveau champ lp_racine
# (le binaire C a ete recompile pour exposer cette colonne).
# UKP grands gardent les valeurs existantes (BB ne converge pas → pas de lp_racine).
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

# Retire les anciennes lignes BB sur les UKP qui vont etre remesurees
A_REMESURER = {"prob_sac_1", "prob_sac_2", "prob_sac_3", "prob_sac_4", "prob_sac_5",
               "prob_sac_10", "prob_sac_20", "prob_sac_25", "prob_sac_30"}
avant = len(lignes_ukp)
lignes_ukp = [l for l in lignes_ukp
              if not (l["instance"] in A_REMESURER and l["methode"] == "B&B (C)")]
print(f"Retire {avant - len(lignes_ukp)} lignes BB obsoletes pour UKP petits/moyens.")

# Re-mesure BB seul (pas OR, pas besoin de relancer)
from src.benchmark_pousse import _executer_c

instances_petits = ["prob_sac_1.txt", "prob_sac_2.txt", "prob_sac_3.txt",
                    "prob_sac_4.txt", "prob_sac_5.txt", "prob_sac_10.txt"]
instances_moyens = ["prob_sac_20.txt", "prob_sac_25.txt", "prob_sac_30.txt"]

for nom in instances_petits + instances_moyens:
    chemin = cfg.dossier_tests_ukp / nom
    timeout = 35.0 if nom in instances_petits else 65.0
    reps = 5 if nom in instances_petits else 3
    print(f"\n--- {nom} (BB seul, timeout {timeout}s, {reps} reps) ---")
    for r in range(1, reps + 1):
        result = _executer_c(cfg.binaire_c, "ukp", chemin, timeout)
        if result is None or result.get("timeout"):
            ligne = {
                "instance": chemin.stem, "n": 0,
                "methode": "B&B (C)", "rep": r, "valeur": 0,
                "temps_s": timeout, "noeuds_generes": 0, "memoire_kb": 0,
                "statut": "TIMEOUT", "timeout_s": timeout, "lp_racine": 0.0,
            }
            print(f"  [{r}/{reps}] TIMEOUT")
        else:
            ligne = {
                "instance": result["instance"], "n": 0,
                "methode": "B&B (C)", "rep": r, "valeur": result["valeur"],
                "temps_s": result["temps_s"], "noeuds_generes": result["noeuds_generes"],
                "memoire_kb": 0, "statut": "OK", "timeout_s": timeout,
                "lp_racine": result.get("lp_racine", 0.0),
            }
            print(f"  [{r}/{reps}] val={result['valeur']:<10} t={result['temps_s']:.4f}s "
                  f"LP={result.get('lp_racine', 0):.2f}")
        # n depuis CSV existant
        for autre in lignes_ukp:
            if autre["instance"] == chemin.stem and autre.get("n"):
                ligne["n"] = autre["n"]
                break
        lignes_ukp.append(ligne)

champs_brut = ["instance", "n", "methode", "rep", "valeur", "temps_s",
               "noeuds_generes", "memoire_kb", "statut", "timeout_s", "lp_racine"]
_ecrire_csv(cfg.dossier_resultats / "ukp_brut.csv", lignes_ukp, champs_brut)
_ecrire_csv(cfg.dossier_resultats / "tsp_brut.csv", lignes_tsp, champs_brut)

champs_agg = ["instance", "methode", "n", "reps", "n_ok",
              "median", "min", "max", "stddev", "valeur_obj_median"]
_ecrire_csv(cfg.dossier_resultats / "ukp_agrege_temps.csv",
            _agreger(lignes_ukp, "temps_s"), champs_agg)
_ecrire_csv(cfg.dossier_resultats / "tsp_agrege_temps.csv",
            _agreger(lignes_tsp, "temps_s"), champs_agg)

print("\nGénération des figures...")
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

print("\n=== AUDIT QUALITE ===")
auditer_qualite(lignes_ukp, lignes_tsp, cfg.dossier_tests_ukp)
print("\nVALIDATION FINALE TERMINEE")
PY
