#!/usr/bin/env bash
cd "$(dirname "$0")/.."
PY="OR-Tools/.venv/bin/python3"

"$PY" - <<'PY'
import sys
sys.path.insert(0, "OR-Tools")
from src.parsers import lire_ukp
from ortools.linear_solver import pywraplp

probleme = lire_ukp("Fichiers tests - Sac à dos-20260510/prob_sac_20.txt")
print(f"n = {probleme.n}, c = {probleme.capacite}")

for nom_solveur in ("CBC", "SCIP", "BOP"):
    solver = pywraplp.Solver.CreateSolver(nom_solveur)
    if solver is None:
        print(f"\n--- {nom_solveur} : indisponible ---")
        continue
    print(f"\n--- {nom_solveur} ---")
    variables = [
        solver.IntVar(0, probleme.capacite // max(probleme.volumes[j], 1), f"x{j+1}")
        for j in range(probleme.n)
    ]
    contrainte = solver.Constraint(0, probleme.capacite, "cap")
    for j, x in enumerate(variables):
        contrainte.SetCoefficient(x, probleme.volumes[j])
    obj = solver.Objective()
    for j, x in enumerate(variables):
        obj.SetCoefficient(x, probleme.utilites[j])
    obj.SetMaximization()
    statut = solver.Solve()
    libelles = {0: "OPTIMAL", 1: "FEASIBLE", 2: "INFEASIBLE", 3: "UNBOUNDED",
                4: "ABNORMAL", 5: "MODEL_INVALID", 6: "NOT_SOLVED"}
    print(f"  statut = {libelles.get(statut, statut)}")
    print(f"  obj    = {obj.Value():.0f}")
    print(f"  vars   = ", end="")
    for j, x in enumerate(variables):
        v = int(round(x.solution_value()))
        if v > 0:
            print(f"x{j+1}={v} ", end="")
    print()
PY
