# Correctness validation

The current evidence is a small-instance correctness check, run once on 2026-09-12 under Ubuntu WSL2. It is not a performance benchmark. No warm-up runs or timing aggregates were used. [CSV](../bench/results/2026-09-12/verification.csv), [JSON with environment](../bench/results/2026-09-12/verification.json), [raw output](../bench/results/2026-09-12/verification.log) and [build log](../bench/results/2026-09-12/build.log) are retained.

## Environment and protocol

| Component | Recorded environment |
|---|---|
| CPU | 13th Gen Intel Core i9-13900H |
| CPU visibility | 20 logical CPUs visible to WSL; no affinity enforced |
| Memory visibility | WSL memory total recorded in the JSON; no per-solver peak RAM claim |
| System | Ubuntu 24.04.4 LTS, WSL2 kernel 6.6.87.2 |
| C toolchain | GCC 13.3.0, GNU Make 4.3, GLPK 5.0 |
| Build | Existing C11 Makefile, `-O2` and its warning flags; full command in build log |
| Python | 3.12.3 |
| Packages | OR-Tools 9.15.6755, NumPy 2.5.3, Matplotlib 3.11.2; [full freeze](../bench/results/2026-09-12/requirements.txt) |
| Runs | One pass per instance, no warm-up |
| Time limits | C process: 90 seconds; OR-Tools UKP: 10 seconds; OR-Tools TSP: 1 second |

Run from the repository root after the installation steps in the README:

```bash
PYTHON=.venv/bin/python bash bench/run.sh
```

The runner writes to `bench/results/local/` by default. The recorded snapshot was created with `bash bench/run.sh bench/results/2026-09-12` using the pinned Python environment. Its JSON records the solver source revision and a SHA-256 digest of the validation script. No application source changed during the overhaul.

UKP reference values come from dynamic programming over integer capacities, allowing repeated items. TSP reference values come from Held-Karp dynamic programming over subsets. Both references share the project parsers. Python assignments are checked for integer nonnegative counts, capacity and utility consistency; tours are checked for visiting every vertex once and for their stated length. C is checked through its objective result, not through an independent reconstruction of its assignment or tour.

## Observed objectives

| Problem | Instance | Exact reference | C | OR-Tools |
|---|---|---:|---:|---:|
| UKP | prob_sac_1 | 13 | 13 | 13 |
| UKP | prob_sac_2 | 66 | 66 | 66 |
| UKP | prob_sac_3 | 51 | 51 | 51 |
| UKP | prob_sac_4 | 132 | 132 | 132 |
| UKP | prob_sac_5 | 199 | 199 | 199 |
| UKP | prob_sac_10 | 285932 | 285932 | 285932 |
| UKP | prob_sac_20 | 125950 | 125950 | 125942 |
| UKP | prob_sac_25 | 285935 | 285935 | 285934 |
| UKP | prob_sac_30 | 95960 | 95960 | 95960 |
| TSP | pd_5 | 20 | 20 | 20 |
| TSP | pd_11 | 156 | 156 | 156 |
| TSP | pd_15 | 284 | 284 | 284 |
| TSP | graphe_12 | 23 | 23 | 23 |
| TSP | graphe_13 | 26 | 26 | 26 |
| TSP | graphe_14 | 29 | 29 | 29 |
| TSP | graphe_15 | 29 | 29 | 29 |

C matched all sixteen reference objectives. Python returned feasible solutions for all sixteen and matched fourteen reference objectives. CBC reported `OPTIMAL` for both discrepant UKP cases. Those discrepancies are accepted as explicitly named known limitations in the regression check; any other mismatch fails it. A future exact result on either case is accepted too. The internal reason for CBC's reported status has not been established here.

All seven TSP heuristic objectives happened to match the references in this run. RoutingModel still reports `OPTIMAL_OU_FAISABLE`; it does not establish optimality for arbitrary instances.

The check keeps the applications' existing search settings and does not override a random seed. A time-limited search can return different objectives on another machine; the reference comparison makes such a difference visible.

## Limits and retained material

Raw C wall time includes process startup and output capture. C internal time and OR-Tools internal time use their existing, different measurement boundaries. These values are diagnostic observations, not a speedup result. Peak memory, scaling and cluster performance are **not measured**, because this utility revision only exercises the bounded correctness protocol.

The larger supplied instances, pd_18/pd_20/pd_22/pd_59, figure generation, LaTeX builds and Romeo scripts were not revalidated. Linux CI is configured to use the same runner; a hosted CI result is pending publication.

`Resultats/` retains historical CSVs and images. `rapport/` retains the original French report, presentation and PDF deliverables. Their old performance narrative is distinct from the evidence above. The supplied coursework text and problem instances have no verified redistribution license in the repository; their original attribution and content are retained, apart from the requested punctuation cleanup in two text documents.
