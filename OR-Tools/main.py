from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.benchmark import ConfigBenchmark, lancer_benchmark
from src.benchmark_pousse import ConfigBenchmarkPousse, lancer_benchmark_pousse
from src.parsers import lire_tsp, lire_ukp
from src.tsp_solver import resoudre_tsp
from src.ukp_solver import resoudre_ukp
from src.visualization import tracer_solution_ukp, tracer_tour_tsp

_RACINE_PROJET = Path(__file__).resolve().parent.parent
_DOSSIER_TESTS_UKP = _RACINE_PROJET / "Fichiers tests - Sac à dos-20260510"
_DOSSIER_TESTS_TSP = _RACINE_PROJET / "Fichiers tests - Voyageur de commerce-20260510"
_DOSSIER_RESULTATS = _RACINE_PROJET / "Resultats"

def _construire_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="or-tools-solveur",
        description="Solveur OR-Tools — UKP & TSP (CHPS_0805).",
    )
    parser.add_argument("-p", "--probleme", choices=["ukp", "tsp"],
                        help="Type de problème à résoudre.")
    parser.add_argument("-f", "--fichier", type=Path,
                        help="Chemin de l'instance (format auto-détecté).")
    parser.add_argument("-t", "--timeout", type=float, default=10.0,
                        help="Timeout en secondes (défaut : 10).")
    parser.add_argument("--visu", action="store_true",
                        help="Génère un PNG de la solution dans Resultats/visualisations/.")
    parser.add_argument("--export", type=Path,
                        help="Répertoire d'export CSV (défaut : Resultats/solutions/).")
    parser.add_argument("--benchmark", action="store_true",
                        help="Lance le benchmark complet (UKP + TSP, BB + OR-Tools).")
    parser.add_argument("--benchmark-pousse", action="store_true",
                        help="Lance le benchmark exhaustif (multi-rep, mémoire, boxplots).")
    parser.add_argument("--reps-petits", type=int, default=5,
                        help="Nombre de répétitions sur les petites instances (def: 5).")
    parser.add_argument("--reps-moyens", type=int, default=3,
                        help="Nombre de répétitions sur les instances moyennes (def: 3).")
    parser.add_argument("--reps-grands", type=int, default=2,
                        help="Nombre de répétitions sur les grandes instances (def: 2).")
    parser.add_argument("--inclure-grands", action="store_true",
                        help="Avec --benchmark[-pousse] : inclut les très grandes instances.")
    parser.add_argument("--phase", action="append", default=None,
                        choices=["ukp_petits", "ukp_moyens", "ukp_grands",
                                 "tsp_petits", "tsp_moyens", "tsp_grands"],
                        help="Restreindre --benchmark-pousse a certaines phases (repetable).")
    parser.add_argument("--accumuler", action="store_true",
                        help="Charge les CSV existants et complete les instances manquantes.")
    parser.add_argument("--binaire-c", type=Path,
                        default=_RACINE_PROJET / "Separation-Evaluation" / "bin" / "solveur",
                        help="Chemin du binaire C (utilisé par --benchmark).")
    parser.add_argument("--visualize", nargs=2, metavar=("TYPE", "INSTANCE"),
                        help="Visualise la solution sans afficher tout le détail. TYPE = ukp|tsp.")
    return parser

def _exporter_csv(probleme_nom: str, dest: Path, lignes: list[dict], champs: list[str]) -> None:
    import csv as _csv

    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", newline="", encoding="utf-8") as f:
        writer = _csv.DictWriter(f, fieldnames=champs)
        writer.writeheader()
        for ligne in lignes:
            writer.writerow({k: ligne.get(k, "") for k in champs})
    print(f"  -> CSV : {dest}")

def _resoudre_ukp_instance(args: argparse.Namespace) -> int:
    probleme = lire_ukp(args.fichier)
    print(f"Probleme UKP : {probleme.nom} (n = {probleme.n}, capacité = {probleme.capacite})")
    sol = resoudre_ukp(probleme, timeout_s=args.timeout)
    print(f"  Statut          : {sol.statut}")
    print(f"  Utilité totale  : {sol.utilite_totale}")
    print(f"  Volume utilisé  : {sol.volume_total} / {probleme.capacite}")
    print(f"  Temps           : {sol.temps_secondes:.6f} s")
    if probleme.n <= 30:
        affectation = ", ".join(
            f"x{j + 1}={v}" for j, v in enumerate(sol.valeurs) if v > 0
        )
        print(f"  Affectation     : {affectation or '(aucune)'}")

    if args.visu:
        chemin = _DOSSIER_RESULTATS / "visualisations" / f"sac_{probleme.nom}_solution.png"
        tracer_solution_ukp(probleme, sol.valeurs, sol.utilite_totale, sol.volume_total, chemin)
        print(f"  -> Visualisation : {chemin}")

    if args.export:
        dest = args.export / f"{probleme.nom}_or.csv"
        _exporter_csv(probleme.nom, dest,
                      [{
                          "instance": probleme.nom,
                          "n": probleme.n,
                          "capacite": probleme.capacite,
                          "valeur": sol.utilite_totale,
                          "volume": sol.volume_total,
                          "temps_s": sol.temps_secondes,
                          "noeuds": sol.n_noeuds,
                          "statut": sol.statut,
                      }],
                      ["instance", "n", "capacite", "valeur", "volume", "temps_s", "noeuds", "statut"])
    return 0

def _resoudre_tsp_instance(args: argparse.Namespace) -> int:
    probleme = lire_tsp(args.fichier)
    print(f"Probleme TSP : {probleme.nom} (n = {probleme.n})")
    sol = resoudre_tsp(probleme, timeout_s=args.timeout)
    print(f"  Statut          : {sol.statut}")
    print(f"  Longueur        : {sol.longueur}")
    print(f"  Temps           : {sol.temps_secondes:.6f} s")
    if probleme.n <= 30:
        print(f"  Tour            : {' '.join(map(str, sol.tour))} -> {sol.tour[0]}")

    if args.visu:
        chemin = _DOSSIER_RESULTATS / "visualisations" / f"tsp_{probleme.nom}_tour.png"
        tracer_tour_tsp(probleme, sol.tour, sol.longueur, chemin)
        print(f"  -> Visualisation : {chemin}")

    if args.export:
        dest = args.export / f"{probleme.nom}_or.csv"
        _exporter_csv(probleme.nom, dest,
                      [{
                          "instance": probleme.nom,
                          "n": probleme.n,
                          "valeur": sol.longueur,
                          "temps_s": sol.temps_secondes,
                          "statut": sol.statut,
                      }],
                      ["instance", "n", "valeur", "temps_s", "statut"])
    return 0

def _commande_visualize(type_probleme: str, fichier: Path) -> int:
    if type_probleme == "ukp":
        probleme = lire_ukp(fichier)
        sol = resoudre_ukp(probleme)
        chemin = _DOSSIER_RESULTATS / "visualisations" / f"sac_{probleme.nom}_solution.png"
        tracer_solution_ukp(probleme, sol.valeurs, sol.utilite_totale, sol.volume_total, chemin)
        print(f"-> {chemin}")
    elif type_probleme == "tsp":
        probleme = lire_tsp(fichier)
        sol = resoudre_tsp(probleme)
        chemin = _DOSSIER_RESULTATS / "visualisations" / f"tsp_{probleme.nom}_tour.png"
        tracer_tour_tsp(probleme, sol.tour, sol.longueur, chemin)
        print(f"-> {chemin}")
    else:
        print(f"Type inconnu : {type_probleme}", file=sys.stderr)
        return 2
    return 0

def main(argv: list[str] | None = None) -> int:
    args = _construire_parser().parse_args(argv)

    if args.benchmark:
        cfg = ConfigBenchmark(
            racine=_RACINE_PROJET,
            binaire_c=args.binaire_c,
            dossier_tests_ukp=_DOSSIER_TESTS_UKP,
            dossier_tests_tsp=_DOSSIER_TESTS_TSP,
            dossier_resultats=_DOSSIER_RESULTATS / "benchmarks",
            timeout_s=args.timeout,
            inclure_grands=args.inclure_grands,
            visualiser=True,
        )
        lancer_benchmark(cfg)
        return 0

    if args.benchmark_pousse:
        phases_par_defaut = ("ukp_petits", "ukp_moyens", "ukp_grands",
                             "tsp_petits", "tsp_moyens", "tsp_grands")
        cfg = ConfigBenchmarkPousse(
            racine=_RACINE_PROJET,
            binaire_c=args.binaire_c,
            dossier_tests_ukp=_DOSSIER_TESTS_UKP,
            dossier_tests_tsp=_DOSSIER_TESTS_TSP,
            dossier_resultats=_DOSSIER_RESULTATS / "benchmarks_pousses",
            inclure_grands=args.inclure_grands,
            reps_petits=args.reps_petits,
            reps_moyens=args.reps_moyens,
            reps_grands=args.reps_grands,
            visualiser=True,
            phases=tuple(args.phase) if args.phase else phases_par_defaut,
            accumuler=args.accumuler,
        )
        lancer_benchmark_pousse(cfg)
        return 0

    if args.visualize:
        return _commande_visualize(args.visualize[0], Path(args.visualize[1]))

    if not args.probleme or not args.fichier:
        _construire_parser().print_help()
        return 2

    if args.export is None:
        args.export = _DOSSIER_RESULTATS / "solutions"

    if args.probleme == "ukp":
        return _resoudre_ukp_instance(args)
    return _resoudre_tsp_instance(args)

if __name__ == "__main__":
    raise SystemExit(main())
