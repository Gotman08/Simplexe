# Reproducible validation

`PYTHON=.venv/bin/python bash bench/run.sh` builds C and runs the reference checks and CLI examples from any working directory. Install the root README prerequisites first. Output defaults to the ignored `bench/results/local/` directory; supply another directory as the first argument to save a separate run.

The runner performs one correctness pass with no warm-up. Raw internal and wall times are retained for diagnosis, but they use different measurement boundaries and are not a speed comparison. It deliberately does not invoke the historical experiment scripts or generate a performance figure. The [recorded snapshot](results/2026-09-12/) backs the repository's current claims.

`tests/verify.py` exits with an error on an invalid solution, an unexpected objective difference, a C timeout or an invalid result row. The two documented CBC objective discrepancies remain visible in CSV/JSON and are accepted as known limitations, not relabelled as exact solutions. If CBC returns the reference objective on those inputs, that result also passes.

On native Linux, the snapshot records the current Git revision automatically. With a Git worktree created by Windows Git, set `SOURCE_REVISION` to its `git rev-parse HEAD` output before running through WSL, because the Windows worktree metadata may not resolve from Linux Git.
