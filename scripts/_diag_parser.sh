#!/usr/bin/env bash
cd "$(dirname "$0")/.."
PY="OR-Tools/.venv/bin/python3"

"$PY" - <<'PY'
import sys
sys.path.insert(0, "OR-Tools")
from src.parsers import lire_ukp

p = lire_ukp("Fichiers tests - Sac à dos-20260510/prob_sac_20.txt")
print(f"n = {p.n}, c = {p.capacite}")
for j in range(p.n):
    print(f"  x{j+1}: volume={p.volumes[j]}, utility={p.utilites[j]}")

# Verify BB solution: x1=4, x2=3, x5=1, x6=1
sel = [(0, 4), (1, 3), (4, 1), (5, 1)]
v = sum(qty * p.volumes[j] for j, qty in sel)
u = sum(qty * p.utilites[j] for j, qty in sel)
print(f"\nBB solution check: volume={v} (cap={p.capacite}), utility={u}, feasible={v <= p.capacite}")
PY
