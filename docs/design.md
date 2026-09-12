# Design and scope

The project compares two implementations over shared coursework datasets. The existing C and Python directories are retained because their imports, shell scripts, report assets and dataset paths depend on this layout.

| Layer | C implementation | Python implementation |
|---|---|---|
| Input | UKP LP/direct parsers; explicit graph/TSPLIB parser | Equivalent formats exposed as dataclasses |
| UKP | Iterative branch-and-bound; GLPK LP bounds | Integer variables and a capacity constraint through CBC |
| TSP | Best-first branch-and-bound; Prim spanning-tree bound | RoutingModel; cheapest-arc initialization and guided local search |
| Output | Console and CSV | Console, CSV and optional Matplotlib PNGs |

The C UKP search uses a greedy incumbent to prune LP-bounded branches. The TSP search bounds a tour with a spanning tree on vertices other than the starting vertex plus two incident edges. The Python TSP search deliberately uses a different search strategy and a fixed time budget, so a faster C completion and an OR-Tools time limit do not measure the same stopping condition.

No evidence of a documented design decision against other solvers or algorithms was found. An exact dynamic program is added only as a small-instance test oracle. It is not substituted into the applications. No solver logic, parser or timing implementation is changed by the overhaul.

## Validation boundary

[tests/verify.py](../tests/verify.py) checks C objectives against unbounded-knapsack dynamic programming and Held-Karp TSP references. It also checks Python assignment/tour feasibility and objective consistency. The reference algorithms are separate from the solver implementations but share the supplied parsers. The test fails on C mismatches, invalid Python solutions or unexpected Python objective discrepancies. The two previously observed CBC discrepancies are recorded as known limitations; an exact result on either case is also accepted.

## Historical experiment limits

The original benchmark runners reuse the Python process and estimate per-call memory by subtracting process peak RSS readings. That difference is not an independently measured per-instance peak and can be zero. C processes are externally terminated on timeout, without a guaranteed exported incumbent. Node counters differ across solvers, and RoutingModel does not expose the same node metric.

The original figures and report are retained as historical deliverables. Their speedups, cluster resource estimates and explanations of compiler effects are not new findings. A future comparison would need isolated processes, a declared quality target, repeated runs and separate treatment of search time and proof of optimality.
