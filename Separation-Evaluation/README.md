# C branch-and-bound application

The UKP solver uses an iterative search, a value-to-volume heuristic and GLPK LP relaxations. The TSP solver uses a best-first search, a minimum spanning tree bound, a nearest-neighbour initial tour and optional 2-opt post-processing. These implementations consolidate the CHPS_0805 TP3 and TP5 exercises.

## Build and usage

From the repository root under Linux or WSL:

```bash
sudo apt-get install build-essential libglpk-dev
make -C Separation-Evaluation -j2
make -C Separation-Evaluation run-test
timeout 30 Separation-Evaluation/bin/solveur --probleme ukp \
  --fichier 'Fichiers tests - Sac à dos-20260510/prob_sac_1.txt'
timeout 30 Separation-Evaluation/bin/solveur --probleme tsp \
  --fichier 'Fichiers tests - Voyageur de commerce-20260510/pd_5.tsp' --silent
```

The [recorded build](../bench/results/2026-09-12/build.log) completed without warnings with GCC 13.3.0 and GLPK 5.0. `make run-test` prints two examples; the asserting reference check is [tests/verify.py](../tests/verify.py).

| Option | Purpose |
|---|---|
| `--probleme ukp\|tsp` | Select the problem |
| `--fichier PATH` | Read a supplied instance |
| `--export DIR` | Export a summary CSV |
| `--verbose` | Print detailed progress |
| `--silent` | Print one result row for a caller |
| `--no-2opt` | Disable TSP post-processing |

The UKP output row contains instance, objective, volume, internal seconds, generated nodes and root LP bound. The TSP row contains instance, objective, internal seconds and generated nodes.

## Scope

The parsers handle the supplied LP/direct UKP files, explicit TSP graphs and EUC_2D coordinate instances. C objectives matched the exact references on all sixteen checked cases. This finite check does not prove correctness on arbitrary input.

The CLI has no effective time limit. A caller can stop the process with `timeout`, but cannot assume it will receive an incumbent solution after termination. Larger instances were not included in the new validation. The existing POSIX build is validated under Ubuntu WSL2, not native Windows.

Public headers are in `include/` and implementations in `src/`. `make -C Separation-Evaluation doc` generates the existing Doxygen documentation when Doxygen is installed; that target was not exercised in this revision.
