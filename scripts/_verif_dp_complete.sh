#!/usr/bin/env bash
# Verification DP exhaustive de toutes les instances UKP testables
# Compare DP (=optimum garanti) avec BB(C) et OR-Tools(CBC)
set -e
cd "$(dirname "$0")/.."
PY="OR-Tools/.venv/bin/python3"

"$PY" - <<'PY'
import sys, time
sys.path.insert(0, "OR-Tools")
from pathlib import Path
from src.parsers import lire_ukp
from src.ukp_solver import resoudre_ukp

def dp_ukp(p):
    """DP unbounded knapsack : f[w] = utilite optimale avec volume <= w."""
    W = p.capacite
    f = [0] * (W + 1)
    for w in range(1, W + 1):
        best = f[w-1]
        for j in range(p.n):
            v = p.volumes[j]
            if v <= w:
                cand = f[w - v] + p.utilites[j]
                if cand > best:
                    best = cand
        f[w] = best
    return f[W]

dossier = Path("Fichiers tests - Sac à dos-20260510")
instances = ["prob_sac_1.txt", "prob_sac_2.txt", "prob_sac_3.txt",
             "prob_sac_4.txt", "prob_sac_5.txt", "prob_sac_10.txt",
             "prob_sac_20.txt", "prob_sac_25.txt", "prob_sac_30.txt",
             "prob_sac_2000.txt", "prob_sac_20000.txt"]

print(f"{'Instance':<22} {'n':<6} {'cap':<10} {'DP':<12} {'OR-Tools':<12} {'OR vs DP':<10} {'temps DP':<10}")
print("=" * 95)
for f in instances:
    chemin = dossier / f
    if not chemin.exists():
        print(f"{f:<22} (introuvable)")
        continue
    p = lire_ukp(chemin)
    # Skip DP for huge instances
    if p.capacite > 200_000 or p.n * p.capacite > 10_000_000:
        print(f"{p.nom:<22} {p.n:<6} {p.capacite:<10} {'(DP skip)':<12}")
        continue
    t0 = time.perf_counter()
    opt = dp_ukp(p)
    t1 = time.perf_counter()

    sol = resoudre_ukp(p, timeout_s=60.0)
    diff = sol.utilite_totale - opt
    flag = "  OK" if diff == 0 else (f"  ⚠ -{-diff}" if diff < 0 else f"  ⚠ +{diff}")
    print(f"{p.nom:<22} {p.n:<6} {p.capacite:<10} {opt:<12} {sol.utilite_totale:<12} {flag:<10} {t1-t0:.3f}s")
PY
