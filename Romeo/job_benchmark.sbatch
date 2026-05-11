#!/bin/bash
#SBATCH --job-name=chps0805-bench
#SBATCH --output=logs/bench_%j.out
#SBATCH --error=logs/bench_%j.err
#SBATCH --partition=normal
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G

# ------------------------------------------------------------------
#  Job SLURM pour le benchmark exhaustif CHPS_0805 (TSP + UKP)
#  - Compile la partie C (Separation-Evaluation) avec GLPK
#  - Configure un venv Python avec OR-Tools
#  - Execute le benchmark exhaustif (toutes instances, 5 rep, timeouts adaptes)
#  - Genere CSV detailles + figures (panneau, boxplots, scaling)
#  - Les resultats apparaissent dans Resultats/benchmarks_pousses/
# ------------------------------------------------------------------

set -euo pipefail

cd "${SLURM_SUBMIT_DIR:-$(pwd)}"
mkdir -p logs

echo "============================================================"
echo "  CHPS_0805 - Benchmark exhaustif Branch&Bound vs OR-Tools"
echo "  Job ID    : ${SLURM_JOB_ID:-local}"
echo "  Node      : $(hostname)"
echo "  Date      : $(date)"
echo "  CPUs      : ${SLURM_CPUS_PER_TASK:-?}"
echo "  Memoire   : ${SLURM_MEM_PER_NODE:-?} MB"
echo "============================================================"

# ---- Modules Romeo (adapter selon les modules disponibles) ----
# Decommenter et adapter si necessaire :
# module purge
# module load gcc/13.3.0
# module load python/3.12
# module load glpk/5.0

if ! command -v gcc >/dev/null; then
    echo "ERREUR : gcc introuvable. Charger un module gcc."
    exit 1
fi

# ---- Compilation C ----
echo
echo "[1/3] Compilation Separation-Evaluation"
cd Separation-Evaluation
make clean
make
cd ..

# ---- Environnement Python ----
echo
echo "[2/3] Configuration venv Python"
if [[ ! -d OR-Tools/.venv ]]; then
    python3 -m venv OR-Tools/.venv
fi
OR-Tools/.venv/bin/pip install -q --upgrade pip
OR-Tools/.venv/bin/pip install -q -r OR-Tools/requirements.txt

# ---- Benchmark exhaustif ----
echo
echo "[3/3] Benchmark exhaustif (peut durer 2-4h)"
OR-Tools/.venv/bin/python OR-Tools/main.py --benchmark-pousse \
    --inclure-grands \
    --reps-petits 5 \
    --reps-moyens 3 \
    --reps-grands 2 \
    --binaire-c "$(pwd)/Separation-Evaluation/bin/solveur"

echo
echo "============================================================"
echo "  Termine. Resultats : Resultats/benchmarks_pousses/"
echo "  Date fin : $(date)"
echo "============================================================"
