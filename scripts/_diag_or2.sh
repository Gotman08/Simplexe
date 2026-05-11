#!/usr/bin/env bash
cd "$(dirname "$0")/.."
PY="OR-Tools/.venv/bin/python3"

"$PY" - <<'PY'
import sys
sys.path.insert(0, "OR-Tools")
from src.parsers import lire_ukp
from ortools.linear_solver import pywraplp
from ortools.algorithms.python import knapsack_solver

p = lire_ukp("Fichiers tests - Sac à dos-20260510/prob_sac_20.txt")
print(f"n = {p.n}, c = {p.capacite}")

# Test 1: LP relaxation
print("\n--- Relaxation LP (continue) ---")
solver = pywraplp.Solver.CreateSolver("GLOP")  # LP solver
variables = [solver.NumVar(0, p.capacite / max(p.volumes[j], 1), f"x{j+1}") for j in range(p.n)]
contrainte = solver.Constraint(0, p.capacite, "cap")
for j, x in enumerate(variables):
    contrainte.SetCoefficient(x, p.volumes[j])
obj = solver.Objective()
for j, x in enumerate(variables):
    obj.SetCoefficient(x, p.utilites[j])
obj.SetMaximization()
statut = solver.Solve()
print(f"  LP relaxation = {obj.Value():.4f} (statut={statut})")

# Test 2: Knapsack solver direct (BRANCH_AND_BOUND)
print("\n--- ortools.algorithms.knapsack_solver (UNBOUNDED) ---")
# CAUTION: knapsack_solver suppose 0/1; convertir en repliquant les items
# Skip — pas adapte UKP

# Test 3: CBC sans borne sup
print("\n--- CBC sans borne explicite ---")
solver2 = pywraplp.Solver.CreateSolver("CBC")
solver2.EnableOutput()
variables2 = [solver2.IntVar(0, solver2.infinity(), f"x{j+1}") for j in range(p.n)]
contrainte2 = solver2.Constraint(0, p.capacite, "cap")
for j, x in enumerate(variables2):
    contrainte2.SetCoefficient(x, p.volumes[j])
obj2 = solver2.Objective()
for j, x in enumerate(variables2):
    obj2.SetCoefficient(x, p.utilites[j])
obj2.SetMaximization()
statut2 = solver2.Solve()
print(f"  CBC sans borne = {obj2.Value():.4f} (statut={statut2})")
for j, x in enumerate(variables2):
    v = int(round(x.solution_value()))
    if v > 0:
        print(f"    x{j+1}={v}", end=" ")
print()
PY
