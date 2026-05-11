#!/usr/bin/env bash
# Balayage parametrique CBC / SCIP / BOP sur prob_sac_20 et prob_sac_25.
# Objectif : identifier la cause exacte des anomalies CBC documentees dans
# rapport.tex (sec. Anomalies). Sortie : CSV par instance dans
# Resultats/diagnostics/.
set -e
cd "$(dirname "$0")/.."

# venv local indisponible (symlinks casses) -> python3 systeme
PY="${PY:-python3}"
mkdir -p "Resultats/diagnostics"

"$PY" - <<'PY'
import sys, csv, time, os
sys.path.insert(0, "OR-Tools")
from pathlib import Path
from src.parsers import lire_ukp
from ortools.linear_solver import pywraplp

CONFIGS = [
    ("C0_baseline",              "CBC", ""),
    ("C1_gap_zero",              "CBC", "allowableGap 0 ratioGap 0"),
    ("C2_inttol_serre",          "CBC", "integerTolerance 1e-12"),
    ("C3_sans_heuristiques",     "CBC", "heuristicsOnOff off"),
    ("C4_sans_coupes",           "CBC", "cutsOnOff off"),
    ("C5_sans_presolveur",       "CBC", "preprocess off"),
    ("C6_tout_brut",             "CBC",
     "allowableGap 0 ratioGap 0 integerTolerance 1e-12 "
     "cutsOnOff off heuristicsOnOff off preprocess off"),
    ("C7_SCIP",                  "SCIP", ""),
    ("C8_BOP",                   "BOP",  ""),
]

LIBELLES_STATUT = {
    pywraplp.Solver.OPTIMAL:      "OPTIMAL",
    pywraplp.Solver.FEASIBLE:     "FAISABLE",
    pywraplp.Solver.INFEASIBLE:   "INFAISABLE",
    pywraplp.Solver.UNBOUNDED:    "NON_BORNE",
    pywraplp.Solver.ABNORMAL:     "ANORMAL",
    pywraplp.Solver.NOT_SOLVED:   "NON_RESOLU",
}


def resoudre(prob, nom_solveur, params):
    solver = pywraplp.Solver.CreateSolver(nom_solveur)
    if solver is None:
        return None
    if params:
        solver.SetSolverSpecificParametersAsString(params)
    bornes = [prob.capacite // max(prob.volumes[j], 1) for j in range(prob.n)]
    variables = [solver.IntVar(0, bornes[j], f"x{j+1}") for j in range(prob.n)]
    c = solver.Constraint(0, prob.capacite, "cap")
    for j, x in enumerate(variables):
        c.SetCoefficient(x, prob.volumes[j])
    obj = solver.Objective()
    for j, x in enumerate(variables):
        obj.SetCoefficient(x, prob.utilites[j])
    obj.SetMaximization()
    t0 = time.perf_counter()
    statut = solver.Solve()
    duree = time.perf_counter() - t0
    bruts = [x.solution_value() for x in variables]
    entiers = [int(round(v)) for v in bruts]
    util = sum(e * u for e, u in zip(entiers, prob.utilites))
    vol  = sum(e * v for e, v in zip(entiers, prob.volumes))
    try:
        n_noeuds = solver.nodes()
    except Exception:
        n_noeuds = -1
    return {
        "statut":     LIBELLES_STATUT.get(statut, str(statut)),
        "obj_solver": obj.Value(),
        "util_calc":  util,
        "volume":     vol,
        "temps_s":    duree,
        "n_noeuds":   n_noeuds,
        "bruts":      bruts,
        "entiers":    entiers,
    }


dossier = Path("Fichiers tests - Sac à dos-20260510")
sortie  = Path("Resultats/diagnostics")

for nom_inst in ("prob_sac_20", "prob_sac_25"):
    prob = lire_ukp(dossier / f"{nom_inst}.txt")
    cible = sortie / f"cbc_params_{nom_inst}.csv"
    print(f"\n=== {nom_inst} (n={prob.n}, c={prob.capacite}) ===")
    with cible.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["config", "solveur", "params", "statut",
                    "obj_solver", "util_recalc", "volume",
                    "temps_s", "n_noeuds", "items_nz"])
        for nom, solv, params in CONFIGS:
            res = resoudre(prob, solv, params)
            if res is None:
                print(f"  {nom:<24} {solv:<5} indisponible")
                w.writerow([nom, solv, params, "INDISPONIBLE",
                            "", "", "", "", "", ""])
                continue
            nz = "; ".join(f"x{j+1}={e}"
                           for j, e in enumerate(res["entiers"]) if e > 0)
            print(f"  {nom:<24} {solv:<5} "
                  f"util={res['util_calc']:>7} "
                  f"vol={res['volume']:>7} "
                  f"statut={res['statut']:<10} "
                  f"noeuds={res['n_noeuds']:>6} "
                  f"t={res['temps_s']*1000:6.1f} ms")
            w.writerow([nom, solv, params, res["statut"],
                        res["obj_solver"], res["util_calc"], res["volume"],
                        f"{res['temps_s']:.6f}", res["n_noeuds"], nz])
    print(f"  -> {cible}")
PY
