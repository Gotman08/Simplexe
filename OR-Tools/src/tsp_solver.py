from __future__ import annotations

from dataclasses import dataclass

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from .distances import distance_euc2d
from .parsers import ProblemeTSP
from .timer import Chronometre

@dataclass
class SolutionTSP:
    instance: str
    tour: list[int]
    longueur: int
    temps_secondes: float
    statut: str

def resoudre_tsp(
    probleme: ProblemeTSP,
    timeout_s: float = 10.0,
    metaheuristique: str = "GUIDED_LOCAL_SEARCH",
) -> SolutionTSP:

    n = probleme.n
    distances = probleme.distances
    coords = probleme.coords

    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    if distances:
        def callback_distance(from_index: int, to_index: int) -> int:
            return distances[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]
    else:
        def callback_distance(from_index: int, to_index: int) -> int:
            i = manager.IndexToNode(from_index)
            j = manager.IndexToNode(to_index)
            return distance_euc2d(coords[i][0], coords[i][1],
                                  coords[j][0], coords[j][1])

    transit_index = routing.RegisterTransitCallback(callback_distance)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_index)

    parametres = pywrapcp.DefaultRoutingSearchParameters()
    parametres.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    metaheuristiques = {
        "GUIDED_LOCAL_SEARCH": routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH,
        "SIMULATED_ANNEALING": routing_enums_pb2.LocalSearchMetaheuristic.SIMULATED_ANNEALING,
        "TABU_SEARCH":         routing_enums_pb2.LocalSearchMetaheuristic.TABU_SEARCH,
        "AUTOMATIC":           routing_enums_pb2.LocalSearchMetaheuristic.AUTOMATIC,
    }
    parametres.local_search_metaheuristic = metaheuristiques.get(
        metaheuristique, routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH,
    )
    parametres.time_limit.seconds = max(1, int(timeout_s))

    chrono = Chronometre()
    solution = routing.SolveWithParameters(parametres)
    temps = chrono.ecoule()

    if solution is None:
        return SolutionTSP(
            instance=probleme.nom,
            tour=[],
            longueur=0,
            temps_secondes=temps,
            statut="ECHEC",
        )

    tour: list[int] = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        tour.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))

    longueur = solution.ObjectiveValue()

    return SolutionTSP(
        instance=probleme.nom,
        tour=tour,
        longueur=int(longueur),
        temps_secondes=temps,
        statut="OPTIMAL_OU_FAISABLE",
    )
