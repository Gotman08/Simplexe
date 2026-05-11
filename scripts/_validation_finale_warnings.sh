#!/usr/bin/env bash
# Validation finale: 0 warning C + 0 warning Python (avec -W error).
set -e
cd "$(dirname "$0")/.."

echo "=== 1. Compilation C avec flags stricts ==="
cd Separation-Evaluation
make clean > /dev/null
COUNT=$(make 2>&1 | grep -cE 'warning|error' || true)
if [[ "$COUNT" -eq 0 ]]; then
    echo "  OK : 0 warning, 0 error"
else
    echo "  ERREUR : $COUNT lignes warning/error detectees"
    exit 1
fi
cd ..

echo
echo "=== 2. Imports Python sous -W error ==="
OR-Tools/.venv/bin/python3 -W error -X utf8 - <<'PY'
import warnings
warnings.simplefilter("error")
import sys
sys.path.insert(0, "OR-Tools")
from src import parsers, distances, timer, ukp_solver, tsp_solver
from src import visualization, benchmark, visualization_pousse, benchmark_pousse
print("  OK : tous les modules importes sans warning")
PY

echo
echo "=== 3. Run UKP+TSP+visualisation sous -W error ==="
OR-Tools/.venv/bin/python3 -W error -X utf8 - <<'PY'
import warnings
warnings.simplefilter("error")
import sys
sys.path.insert(0, "OR-Tools")
from pathlib import Path
from src.parsers import lire_ukp, lire_tsp
from src.ukp_solver import resoudre_ukp
from src.tsp_solver import resoudre_tsp
from src.visualization import tracer_solution_ukp, tracer_tour_tsp

p = lire_ukp("Fichiers tests - Sac à dos-20260510/prob_sac_5.txt")
sol = resoudre_ukp(p, timeout_s=5.0)
tracer_solution_ukp(p, sol.valeurs, sol.utilite_totale, sol.volume_total,
                    Path("/tmp/_test.png"))
print(f"  UKP OK : utilite={sol.utilite_totale}")

p = lire_tsp("Fichiers tests - Voyageur de commerce-20260510/pd_5.tsp")
sol = resoudre_tsp(p, timeout_s=2.0)
tracer_tour_tsp(p, sol.tour, sol.longueur, Path("/tmp/_test_tsp.png"))
print(f"  TSP OK : longueur={sol.longueur}")
PY

echo
echo "=== 4. Generation des figures avancees sous -W error ==="
OR-Tools/.venv/bin/python3 -W error -X utf8 - <<'PY'
import warnings
warnings.simplefilter("error")
import sys
sys.path.insert(0, "OR-Tools")
from pathlib import Path
from src.benchmark_pousse import _charger_csv
from src.visualization_pousse import (
    tracer_panneau_principal, tracer_boxplot_temps,
    tracer_scaling_avec_erreurs, tracer_qualite_relative,
    tracer_performance_profile,
)

D = Path("Resultats/benchmarks_pousses")
ukp = _charger_csv(D / "ukp_brut.csv")
tsp = _charger_csv(D / "tsp_brut.csv")

tracer_panneau_principal(ukp, tsp, Path("/tmp/_p.png"))
tracer_boxplot_temps(ukp, "UKP", Path("/tmp/_b1.png"))
tracer_boxplot_temps(tsp, "TSP", Path("/tmp/_b2.png"))
tracer_scaling_avec_erreurs(ukp, "UKP", Path("/tmp/_s1.png"))
tracer_scaling_avec_erreurs(tsp, "TSP", Path("/tmp/_s2.png"))
tracer_qualite_relative(ukp, tsp, Path("/tmp/_q.png"))
tracer_performance_profile(ukp, tsp, Path("/tmp/_pp.png"))
print("  OK : 7 figures generees sans aucun warning")
PY

echo
echo "=== VALIDATION FINALE TERMINEE : 0 WARNING C + 0 WARNING PYTHON ==="
