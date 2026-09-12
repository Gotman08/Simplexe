# Historical coursework experiments

The CSV files and PNGs in this directory were present in the initial repository. They are retained with the French report as historical experiment artifacts. The overhaul did not rerun this full benchmark or validate its performance claims.

Current correctness evidence, environment details and the two reproduced CBC discrepancies are documented in [docs/results.md](../../docs/results.md). The old narrative included claims about compiler speed changes and CBC's internal stopping mechanism that the new validation does not establish; that narrative remains available in Git history at `191b2c1`.

The original CSV and visualization modules remain available through `scripts/make_plots.py` and `OR-Tools/src/visualization_pousse.py`. Regenerating the historical pipeline can overwrite these files. The report references the PNGs here directly, so these paths are preserved.

The earlier dataset is in [benchmarks_pousses_avant](../benchmarks_pousses_avant/ANALYSE.md). Both sets used an identical `qualite_relative.png`; its single retained copy is [here](qualite_relative.png).
