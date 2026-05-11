#!/usr/bin/env bash
# Calcule le gap LP relaxation / vrai optimum pour chaque UKP
set -e
cd "$(dirname "$0")/.."
PY="OR-Tools/.venv/bin/python3"

"$PY" - <<'PY'
import sys
sys.path.insert(0, "OR-Tools")
from pathlib import Path
from src.parsers import lire_ukp
from ortools.linear_solver import pywraplp

def lp_relaxation(p):
    solver = pywraplp.Solver.CreateSolver("GLOP")
    if not solver:
        return None
    variables = [solver.NumVar(0, p.capacite / max(p.volumes[j], 1), f"x{j+1}") for j in range(p.n)]
    contrainte = solver.Constraint(0, p.capacite, "cap")
    for j, x in enumerate(variables):
        contrainte.SetCoefficient(x, p.volumes[j])
    obj = solver.Objective()
    for j, x in enumerate(variables):
        obj.SetCoefficient(x, p.utilites[j])
    obj.SetMaximization()
    if solver.Solve() == pywraplp.Solver.OPTIMAL:
        return obj.Value()
    return None

def dp_ukp(p):
    W = p.capacite
    f = [0] * (W + 1)
    for w in range(1, W + 1):
        best = f[w-1]
        for j in range(p.n):
            v = p.volumes[j]
            if v <= w and f[w-v] + p.utilites[j] > best:
                best = f[w-v] + p.utilites[j]
        f[w] = best
    return f[W]

dossier = Path("Fichiers tests - Sac à dos-20260510")
print(f"{'Instance':<22} {'n':<6} {'opt(int)':<12} {'LP relaxe':<14} {'gap LP-INT':<12} {'gap %':<8}")
print("=" * 80)
for f in ["prob_sac_1.txt", "prob_sac_2.txt", "prob_sac_3.txt",
          "prob_sac_4.txt", "prob_sac_5.txt", "prob_sac_10.txt",
          "prob_sac_20.txt", "prob_sac_25.txt", "prob_sac_30.txt"]:
    p = lire_ukp(dossier / f)
    lp = lp_relaxation(p)
    if p.capacite > 200_000:
        opt = "(skip)"
        gap_str = "(skip)"
        gap_pct_str = "(skip)"
    else:
        opt = dp_ukp(p)
        gap = lp - opt
        gap_pct = 100 * gap / opt if opt else 0.0
        gap_str = f"{gap:.4f}"
        gap_pct_str = f"{gap_pct:.4f}%"
    lp_str = f"{lp:.4f}" if lp else "?"
    opt_str = str(opt) if isinstance(opt, int) else opt
    print(f"{p.nom:<22} {p.n:<6} {opt_str:<12} {lp_str:<14} {gap_str:<12} {gap_pct_str:<8}")
PY
