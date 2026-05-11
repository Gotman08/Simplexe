from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "OR-Tools"))

from src.visualization import tracer_panneau_benchmark

def main() -> int:
    dossier = RACINE / "Resultats" / "benchmarks"
    chemins_csv = {
        "ukp_bb": dossier / "ukp_branch_and_bound.csv",
        "ukp_or": dossier / "ukp_or_tools.csv",
        "tsp_bb": dossier / "tsp_branch_and_bound.csv",
        "tsp_or": dossier / "tsp_or_tools.csv",
    }
    chemins_existants = {k: v for k, v in chemins_csv.items() if v.exists()}
    if not chemins_existants:
        print(f"Aucun CSV trouvé dans {dossier}.", file=sys.stderr)
        return 1
    sortie = dossier / "panneau_benchmark.png"
    tracer_panneau_benchmark(chemins_existants, sortie)
    print(f"-> {sortie}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
