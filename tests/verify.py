"""Check existing solvers against small exact references without changing them."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "OR-Tools"))
from src.parsers import lire_tsp, lire_ukp
from src.tsp_solver import resoudre_tsp
from src.ukp_solver import resoudre_ukp

UKP_CASES = [1, 2, 3, 4, 5, 10, 20, 25, 30]
TSP_CASES = ["pd_5.tsp", "pd_11.tsp", "pd_15.tsp", "graphe_12.txt",
             "graphe_13.txt", "graphe_14.txt", "graphe_15.txt"]
KNOWN_CBC_DISCREPANCIES = {
    "prob_sac_20": (125950, 125942, "OPTIMAL"),
    "prob_sac_25": (285935, 285934, "OPTIMAL"),
}


def exact_ukp(problem):
    """Maximum integer utility for each capacity, allowing repeated items."""
    values = [0] * (problem.capacite + 1)
    for capacity in range(1, problem.capacite + 1):
        values[capacity] = max(
            [values[capacity - 1]] +
            [values[capacity - volume] + utility
             for volume, utility in zip(problem.volumes, problem.utilites)
             if volume <= capacity]
        )
    return values[-1]


def exact_tsp(problem):
    """Held-Karp dynamic programming with vertex zero as the start."""
    distances = problem.distances

    @lru_cache(None)
    def best(mask, last):
        previous = mask ^ (1 << (last - 1))
        if not previous:
            return distances[0][last]
        return min(best(previous, vertex) + distances[vertex][last]
                   for vertex in range(1, problem.n)
                   if previous & (1 << (vertex - 1)))

    full = (1 << (problem.n - 1)) - 1
    return min(best(full, vertex) + distances[vertex][0]
               for vertex in range(1, problem.n))


def run_c(kind, path, timeout):
    command = ["Separation-Evaluation/bin/solveur", "--probleme", kind,
               "--fichier", str(path.relative_to(ROOT)), "--silent"]
    print("COMMAND: " + shlex.join(command), flush=True)
    started = time.perf_counter()
    try:
        process = subprocess.run(command, cwd=ROOT, capture_output=True,
                                 text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        print(f"C TIMEOUT after {timeout} s", flush=True)
        return None, time.perf_counter() - started, None, "TIMEOUT"
    wall = time.perf_counter() - started
    print(process.stdout, end="", flush=True)
    if process.stderr:
        print("STDERR: " + process.stderr, flush=True)
    if process.returncode:
        return None, wall, None, f"EXIT_{process.returncode}"
    try:
        fields = process.stdout.strip().splitlines()[-1].split(",")
        internal_time = float(fields[3 if kind == "ukp" else 2])
        return int(fields[1]), wall, internal_time, "COMPLETED"
    except (ValueError, IndexError):
        return None, wall, None, "INVALID_OUTPUT"


def metadata():
    revision = os.environ.get("SOURCE_REVISION")
    if not revision:
        try:
            revision = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            revision = "unavailable; set SOURCE_REVISION for non-native worktrees"
    cpu = platform.processor()
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        cpu = next((line.split(":", 1)[1].strip()
                    for line in cpuinfo.read_text().splitlines()
                    if line.startswith("model name")), cpu)
    memory = None
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        memory = next((line.split(":", 1)[1].strip()
                       for line in meminfo.read_text().splitlines()
                       if line.startswith("MemTotal:")), None)
    return {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": revision,
        "validation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": sys.version,
        "platform": platform.platform(),
        "cpu": cpu,
        "logical_cpus_visible": os.cpu_count(),
        "memory_visible": memory,
        "packages": {name: importlib.metadata.version(name)
                     for name in ["ortools", "numpy", "matplotlib"]},
        "repetitions": 1,
        "warmup_runs": 0,
        "purpose": "correctness validation; timings are not a performance comparison",
        "parser_scope": "reference algorithms share the project parsers",
    }


def check_cases(c_timeout):
    rows = []
    for kind, cases, directory in [
        ("ukp", [f"prob_sac_{n}.txt" for n in UKP_CASES],
         "Fichiers tests - Sac à dos-20260510"),
        ("tsp", TSP_CASES, "Fichiers tests - Voyageur de commerce-20260510"),
    ]:
        for name in cases:
            path = ROOT / directory / name
            if kind == "ukp":
                problem = lire_ukp(path)
                reference = exact_ukp(problem)
                solution = resoudre_ukp(problem, timeout_s=10)
                objective = solution.utilite_totale
                feasible = (
                    len(solution.valeurs) == problem.n
                    and all(isinstance(value, int) and value >= 0
                            for value in solution.valeurs)
                    and sum(v * x for v, x in zip(problem.volumes, solution.valeurs))
                    == solution.volume_total <= problem.capacite
                    and sum(u * x for u, x in zip(problem.utilites, solution.valeurs))
                    == objective
                )
            else:
                problem = lire_tsp(path)
                reference = exact_tsp(problem)
                solution = resoudre_tsp(problem, timeout_s=1)
                objective = solution.longueur
                tour = solution.tour
                feasible = (
                    len(tour) == problem.n
                    and sorted(tour) == list(range(problem.n))
                    and sum(problem.distances[tour[i]][tour[(i + 1) % problem.n]]
                            for i in range(problem.n)) == objective
                )
            c_value, c_wall, c_internal, c_status = run_c(kind, path, c_timeout)
            known = (kind == "ukp" and KNOWN_CBC_DISCREPANCIES.get(problem.nom)
                     == (reference, objective, solution.statut))
            row = {
                "problem": kind, "instance": problem.nom, "n": problem.n,
                "reference_algorithm": "capacity_dp" if kind == "ukp" else "held_karp",
                "reference": reference, "c_value": c_value,
                "c_wall_s": c_wall, "c_internal_s": c_internal, "c_status": c_status,
                "or_value": objective, "or_reported_s": solution.temps_secondes,
                "or_status": solution.statut, "or_feasible": feasible,
                "c_matches": c_value == reference, "or_matches": objective == reference,
                "known_cbc_discrepancy": known,
            }
            row["unexpected_failure"] = (
                not row["c_matches"] or not feasible
                or (not row["or_matches"] and not known)
            )
            rows.append(row)
            print(json.dumps(row), flush=True)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "bench/results/local")
    parser.add_argument("--c-timeout", type=float, default=90)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    environment = metadata()
    environment["c_process_timeout_s"] = args.c_timeout
    environment["or_ukp_timeout_s"] = 10
    environment["or_tsp_timeout_s"] = 1
    print(json.dumps(environment), flush=True)
    rows = check_cases(args.c_timeout)
    failures = sum(row["unexpected_failure"] for row in rows)
    known = sum(row["known_cbc_discrepancy"] for row in rows)
    with (args.output / "verification.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "verification.json").write_text(
        json.dumps({"environment": environment, "rows": rows,
                    "unexpected_failures": failures, "known_cbc_discrepancies": known},
                   indent=2) + "\n", encoding="utf-8")
    print(f"Checked {len(rows)} cases: {failures} unexpected failures; "
          f"{known} known CBC objective discrepancies", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
