# OR-Tools application

The Python CLI solves UKP through CBC and searches for TSP tours through RoutingModel with PATH_CHEAPEST_ARC and GUIDED_LOCAL_SEARCH. TSP results are feasible candidates, not optimality certificates.

## Setup and usage

Use Linux or WSL with Python 3.12. The imported benchmark module uses Unix `resource`, so the CLI is not portable to native Windows as written. From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r OR-Tools/requirements.txt
.venv/bin/python OR-Tools/main.py --help
.venv/bin/python OR-Tools/main.py --probleme ukp \
  --fichier 'Fichiers tests - Sac à dos-20260510/prob_sac_1.txt' \
  --timeout 10 --export bench/results/local/solutions
.venv/bin/python OR-Tools/main.py --probleme tsp \
  --fichier 'Fichiers tests - Voyageur de commerce-20260510/pd_5.tsp' \
  --timeout 1 --export bench/results/local/solutions
```

`--visu` creates a PNG in `Resultats/visualisations/`. Without an explicit `--export`, ordinary solve commands write into the tracked `Resultats/solutions/` directory. Choose a local export directory when preserving the historical snapshot.

## Modules

`src/parsers.py` reads the supplied UKP and TSP formats. `distances.py` implements rounded EUC_2D distances. `ukp_solver.py` and `tsp_solver.py` expose solver functions. The benchmark and visualization modules drive the original CSV and plotting workflows. The project layout is retained so existing imports and dataset paths continue to work.

## Validation and limitations

Run `PYTHON=.venv/bin/python bash bench/run.sh` from the root. The [recorded check](../docs/results.md) verifies feasibility and compares objectives with exact reference algorithms. CBC reproduces the documented `prob_sac_20` and `prob_sac_25` discrepancies despite its `OPTIMAL` status. The regression check reports those observations explicitly and fails on unexpected discrepancies.

`--benchmark` and `--benchmark-pousse` remain available for the historical experiment pipeline. They can take substantial time and overwrite tracked results. Their TSP time limits and memory measurements require care when interpreting comparisons; see [design notes](../docs/design.md).
