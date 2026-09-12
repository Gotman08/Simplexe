# Simplexe: TSP and unbounded knapsack

C branch-and-bound matches exact reference objectives on **16 checked instances**. OR-Tools returns feasible solutions on all 16, with two UKP objectives below the reference despite an `OPTIMAL` status. [Recorded results](bench/results/2026-09-12/verification.csv).

## Abstract

This individual CHPS_0805 coursework project compares implementations of the travelling salesperson problem (TSP) and unbounded knapsack problem (UKP). The C application combines branch-and-bound with GLPK relaxations for UKP and minimum spanning tree bounds for TSP. The Python application uses OR-Tools CBC for UKP and RoutingModel with guided local search for TSP. The latter is a heuristic search with a time limit. The repository includes the supplied instances, the original report and a reproducible correctness check. Performance comparisons are **not measured (non mesuré)** in this revision because this utility audit validates correctness and did not run a timed comparison. Historical experiments remain separate.

## What works

- The C application builds without compiler warnings in the recorded Ubuntu WSL2 environment. [Build log](bench/results/2026-09-12/build.log).
- Nine UKP and seven TSP cases match independent exact reference algorithms for C. Python returns feasible assignments or tours for all cases and matches the reference objective on fourteen. The references share the project's parsers, so this is not an independent audit of the input formats. [Protocol and results](docs/results.md).
- The Python CLI runs the small UKP and TSP examples and exports CSV files. [CLI log](bench/results/2026-09-12/cli.log).

## What does not work

- CBC returns 125942 instead of 125950 on `prob_sac_20`, and 285934 instead of 285935 on `prob_sac_25`, both with `OPTIMAL` status in the recorded environment. Check objectives against an exact reference before relying on that status. The internal cause has not been established here.
- The TSP RoutingModel result is not an optimality certificate. Matching the small references does not establish exactness on other instances.
- The C CLI has no effective timeout option. External termination can lose the current solution; use a process timeout when exploring larger inputs.
- Large instances, report compilation, figure generation and Romeo cluster execution were not revalidated. Native Windows execution is not supported by the Python benchmark module's Unix `resource` dependency; use WSL.
- Hosted CI has not run on this unpublished branch. Its build and validation commands pass locally under Ubuntu WSL2.

## Install and use

Run these commands from the repository root under Ubuntu 24.04 or WSL2, with Python 3.12:

```bash
sudo apt-get install build-essential libglpk-dev python3-venv
python3 -m venv .venv
.venv/bin/python -m pip install -r OR-Tools/requirements.txt
make -C Separation-Evaluation -j2

timeout 30 Separation-Evaluation/bin/solveur --probleme ukp \
  --fichier 'Fichiers tests - Sac à dos-20260510/prob_sac_1.txt'
.venv/bin/python OR-Tools/main.py --probleme tsp \
  --fichier 'Fichiers tests - Voyageur de commerce-20260510/pd_5.tsp' \
  --timeout 1 --export bench/results/local/solutions

PYTHON=.venv/bin/python bash bench/run.sh
```

The last command rebuilds C, validates both applications and writes local evidence under `bench/results/local/`. It does not launch the historical benchmark pipeline. See the [C CLI](Separation-Evaluation/README.md) and [Python CLI](OR-Tools/README.md) for other options.

## Layout

| Path | Purpose |
|---|---|
| `Separation-Evaluation/` | C sources, headers and Makefile |
| `OR-Tools/` | Python CLI, solvers, parsers and plotting modules |
| `Fichiers tests - */` | Supplied coursework problem instances |
| `tests/`, `bench/` | Reference validation, runner and raw evidence |
| `docs/` | [Design](docs/design.md) and [results](docs/results.md) |
| `Resultats/`, `rapport/` | Historical experiments and French coursework deliverables |
| `Romeo/`, `scripts/` | Original deployment and experiment helpers |

## License

No license grant has been established for the original project. [LICENSE](LICENSE) records the all-rights-reserved status; supplied course material, datasets and dependencies retain their respective owners' terms.
