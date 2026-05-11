#!/usr/bin/env bash
# Verifie qu'aucun warning Python ne sort durant la generation des figures.
set -e
cd "$(dirname "$0")/.."

OR-Tools/.venv/bin/python3 -W default -X utf8 - <<'PY'
import sys
sys.path.insert(0, "OR-Tools")
import warnings
warnings.simplefilter("default")

from pathlib import Path
from src.benchmark_pousse import _charger_csv, auditer_qualite
from src.visualization_pousse import (
    tracer_panneau_principal, tracer_boxplot_temps,
    tracer_scaling_avec_erreurs, tracer_qualite_relative,
    tracer_performance_profile,
)

D = Path("Resultats/benchmarks_pousses")
ukp = _charger_csv(D / "ukp_brut.csv")
tsp = _charger_csv(D / "tsp_brut.csv")

tracer_panneau_principal(ukp, tsp, D / "_test_panneau.png")
tracer_boxplot_temps(ukp, "UKP", D / "_test_box_ukp.png")
tracer_boxplot_temps(tsp, "TSP", D / "_test_box_tsp.png")
tracer_scaling_avec_erreurs(ukp, "UKP", D / "_test_scaling_ukp.png")
tracer_scaling_avec_erreurs(tsp, "TSP", D / "_test_scaling_tsp.png")
tracer_qualite_relative(ukp, tsp, D / "_test_qualite.png")
tracer_performance_profile(ukp, tsp, D / "_test_perf.png")

# Audit
auditer_qualite(ukp, tsp, Path("Fichiers tests - Sac à dos-20260510"))

print("\nOK_NO_WARNINGS")
PY

# Cleanup
rm -f Resultats/benchmarks_pousses/_test_*.png
