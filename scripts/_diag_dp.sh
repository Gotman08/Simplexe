#!/usr/bin/env bash
cd "$(dirname "$0")/.."
PY="OR-Tools/.venv/bin/python3"

"$PY" - <<'PY'
import sys
sys.path.insert(0, "OR-Tools")
from src.parsers import lire_ukp

p = lire_ukp("Fichiers tests - Sac à dos-20260510/prob_sac_20.txt")
print(f"DP exhaustif sur prob_sac_20 (n={p.n}, c={p.capacite})...")

# DP UKP : f[w] = utilite optimale avec volume <= w
W = p.capacite
f = [0] * (W + 1)
choix = [-1] * (W + 1)
for w in range(1, W + 1):
    best, best_j = f[w - 1], -1
    for j in range(p.n):
        if p.volumes[j] <= w:
            cand = f[w - p.volumes[j]] + p.utilites[j]
            if cand > best:
                best = cand
                best_j = j
    f[w] = best
    choix[w] = best_j

util = f[W]
print(f"\nUtilite optimale DP : {util}")

# Reconstruire la solution
qty = [0] * p.n
w = W
while w > 0 and choix[w] >= 0:
    j = choix[w]
    qty[j] += 1
    w -= p.volumes[j]
v_check = sum(qty[j] * p.volumes[j] for j in range(p.n))
u_check = sum(qty[j] * p.utilites[j] for j in range(p.n))
print(f"Volume utilise : {v_check} / {W}")
print(f"Utilite verifiee : {u_check}")
print("Affectation : ", " ".join(f"x{j+1}={qty[j]}" for j in range(p.n) if qty[j] > 0))
PY
