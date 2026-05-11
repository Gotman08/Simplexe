from __future__ import annotations

from dataclasses import dataclass

from ortools.linear_solver import pywraplp

from .parsers import ProblemeUKP
from .timer import Chronometre

@dataclass
class SolutionUKP:
    instance: str
    valeurs: list[int]
    utilite_totale: int
    volume_total: int
    capacite: int
    temps_secondes: float
    n_noeuds: int
    statut: str

def resoudre_ukp(probleme: ProblemeUKP, solveur: str = "CBC", timeout_s: float | None = None) -> SolutionUKP:
    solver = pywraplp.Solver.CreateSolver(solveur)
    if solver is None:
        raise RuntimeError(f"Solveur OR-Tools '{solveur}' indisponible")

    if timeout_s is not None and timeout_s > 0:
        solver.SetTimeLimit(int(timeout_s * 1000))

    variables = [
        solver.IntVar(0, probleme.capacite // max(probleme.volumes[j], 1), f"x{j + 1}")
        for j in range(probleme.n)
    ]

    contrainte = solver.Constraint(0, probleme.capacite, "capacite")
    for j, x in enumerate(variables):
        contrainte.SetCoefficient(x, probleme.volumes[j])

    objectif = solver.Objective()
    for j, x in enumerate(variables):
        objectif.SetCoefficient(x, probleme.utilites[j])
    objectif.SetMaximization()

    chrono = Chronometre()
    statut = solver.Solve()
    temps = chrono.ecoule()

    libelles = {
        pywraplp.Solver.OPTIMAL: "OPTIMAL",
        pywraplp.Solver.FEASIBLE: "FAISABLE",
        pywraplp.Solver.INFEASIBLE: "INFAISABLE",
        pywraplp.Solver.UNBOUNDED: "NON_BORNE",
        pywraplp.Solver.ABNORMAL: "ANORMAL",
        pywraplp.Solver.NOT_SOLVED: "NON_RESOLU",
    }
    libelle = libelles.get(statut, str(statut))

    valeurs: list[int] = []
    utilite_totale = 0
    volume_total = 0
    if statut in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        valeurs = [int(round(x.solution_value())) for x in variables]
        utilite_totale = sum(v * u for v, u in zip(valeurs, probleme.utilites))
        volume_total = sum(v * w for v, w in zip(valeurs, probleme.volumes))

    try:
        n_noeuds = solver.nodes()
    except Exception:
        n_noeuds = -1

    return SolutionUKP(
        instance=probleme.nom,
        valeurs=valeurs,
        utilite_totale=utilite_totale,
        volume_total=volume_total,
        capacite=probleme.capacite,
        temps_secondes=temps,
        n_noeuds=n_noeuds,
        statut=libelle,
    )
