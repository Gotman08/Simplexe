#!/usr/bin/env bash
# Compare item-a-item la solution DP exhaustive vs CBC/OR-Tools sur les
# deux instances en cause (prob_sac_20, prob_sac_25). Caracterise la
# geometrie exacte de la solution manquee par CBC.
set -e
cd "$(dirname "$0")/.."

PY="${PY:-python3}"

"$PY" - <<'PY'
import sys
sys.path.insert(0, "OR-Tools")
from pathlib import Path
from src.parsers import lire_ukp
from ortools.linear_solver import pywraplp


def dp_ukp(prob):
    """DP exhaustive : retourne (utilite_opt, quantites)."""
    W = prob.capacite
    f = [0] * (W + 1)
    choix = [-1] * (W + 1)
    for w in range(1, W + 1):
        best, best_j = f[w - 1], -1
        for j in range(prob.n):
            v = prob.volumes[j]
            if v <= w:
                cand = f[w - v] + prob.utilites[j]
                if cand > best:
                    best, best_j = cand, j
        f[w] = best
        choix[w] = best_j
    qty = [0] * prob.n
    w = W
    while w > 0 and choix[w] >= 0:
        j = choix[w]
        qty[j] += 1
        w -= prob.volumes[j]
    return f[W], qty


def cbc_ukp(prob):
    """Solveur CBC par defaut (formulation identique a ukp_solver.py)."""
    solver = pywraplp.Solver.CreateSolver("CBC")
    variables = [
        solver.IntVar(0, prob.capacite // max(prob.volumes[j], 1), f"x{j+1}")
        for j in range(prob.n)
    ]
    c = solver.Constraint(0, prob.capacite, "cap")
    for j, x in enumerate(variables):
        c.SetCoefficient(x, prob.volumes[j])
    obj = solver.Objective()
    for j, x in enumerate(variables):
        obj.SetCoefficient(x, prob.utilites[j])
    obj.SetMaximization()
    solver.Solve()
    qty = [int(round(x.solution_value())) for x in variables]
    util = sum(q * u for q, u in zip(qty, prob.utilites))
    return util, qty


def lp_relax(prob):
    """Relaxation continue (GLOP) : borne superieure du B&B."""
    solver = pywraplp.Solver.CreateSolver("GLOP")
    variables = [
        solver.NumVar(0, prob.capacite / max(prob.volumes[j], 1), f"x{j+1}")
        for j in range(prob.n)
    ]
    c = solver.Constraint(0, prob.capacite, "cap")
    for j, x in enumerate(variables):
        c.SetCoefficient(x, prob.volumes[j])
    obj = solver.Objective()
    for j, x in enumerate(variables):
        obj.SetCoefficient(x, prob.utilites[j])
    obj.SetMaximization()
    if solver.Solve() == pywraplp.Solver.OPTIMAL:
        return obj.Value(), [x.solution_value() for x in variables]
    return None, None


def diff_resume(prob, qty_dp, qty_cbc):
    """Differences items et structure de la divergence."""
    diff = [(j, qty_dp[j] - qty_cbc[j])
            for j in range(prob.n) if qty_dp[j] != qty_cbc[j]]
    delta_util = sum(d * prob.utilites[j] for j, d in diff)
    delta_vol  = sum(d * prob.volumes[j]  for j, d in diff)
    return diff, delta_util, delta_vol


dossier = Path("Fichiers tests - Sac à dos-20260510")

for nom_inst in ("prob_sac_20", "prob_sac_25"):
    prob = lire_ukp(dossier / f"{nom_inst}.txt")
    print(f"\n{'=' * 72}")
    print(f"  {nom_inst}  (n={prob.n}, capacite={prob.capacite})")
    print(f"{'=' * 72}")

    lp_val, lp_x = lp_relax(prob)
    util_dp, qty_dp = dp_ukp(prob)
    util_cbc, qty_cbc = cbc_ukp(prob)
    vol_dp  = sum(q * v for q, v in zip(qty_dp,  prob.volumes))
    vol_cbc = sum(q * v for q, v in zip(qty_cbc, prob.volumes))
    n_dp  = sum(qty_dp)
    n_cbc = sum(qty_cbc)

    print(f"\n  Borne LP relax (GLOP)   : {lp_val:.6f}")
    print(f"  Optimum DP exhaustif    : {util_dp}  "
          f"(volume={vol_dp}/{prob.capacite}, marge={prob.capacite-vol_dp}, items={n_dp})")
    print(f"  CBC defaut              : {util_cbc}  "
          f"(volume={vol_cbc}/{prob.capacite}, marge={prob.capacite-vol_cbc}, items={n_cbc})")
    print(f"  Gap CBC vs DP           : {util_dp - util_cbc} "
          f"({(util_dp - util_cbc)/util_dp*100:.4f}%)")
    print(f"  Gap LP-INT (vrai)       : {lp_val - util_dp:.4f}")
    print(f"  Gap LP-CBC (vu de CBC)  : {lp_val - util_cbc:.4f}")

    diff, dU, dV = diff_resume(prob, qty_dp, qty_cbc)
    print(f"\n  Differences items (DP - CBC) -> Delta util = {dU}, Delta vol = {dV}:")
    print(f"  {'item':>4} {'vol':>7} {'util':>7} {'qty_DP':>7} {'qty_CBC':>8} {'delta':>6}")
    for j, d in diff:
        print(f"  x{j+1:<3} {prob.volumes[j]:>7} {prob.utilites[j]:>7} "
              f"{qty_dp[j]:>7} {qty_cbc[j]:>8} {d:>+6}")

    items_cbc = [(j + 1, qty_cbc[j]) for j in range(prob.n) if qty_cbc[j] > 0]
    items_dp  = [(j + 1, qty_dp[j])  for j in range(prob.n) if qty_dp[j]  > 0]
    print(f"\n  Items DP  : {items_dp}")
    print(f"  Items CBC : {items_cbc}")

    print(f"\n  LP relaxe (5 plus gros) :")
    paires = sorted(enumerate(lp_x), key=lambda t: -t[1])[:5]
    for j, v in paires:
        if v > 1e-9:
            print(f"    x{j+1:<3} = {v:.6f}  (vol={prob.volumes[j]}, "
                  f"util={prob.utilites[j]}, ratio u/v={prob.utilites[j]/prob.volumes[j]:.6f})")
PY
