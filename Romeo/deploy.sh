#!/usr/bin/env bash
# Deploiement du projet sur Romeo via rsync
#
# Usage :
#   bash Romeo/deploy.sh                          # avec defaut
#   ROMEO_USER=login Romeo/deploy.sh              # specifie le login
#   ROMEO_HOST=romeo2.univ-reims.fr ...           # specifie l'host
#   ROMEO_DEST=/scratch/$USER/chps0805 ...        # destination

set -euo pipefail

cd "$(dirname "$0")/.."
RACINE="$(pwd)"

ROMEO_USER="${ROMEO_USER:-$USER}"
ROMEO_HOST="${ROMEO_HOST:-romeo.univ-reims.fr}"
ROMEO_DEST="${ROMEO_DEST:-/home/$ROMEO_USER/chps0805}"

echo "Source      : $RACINE"
echo "Destination : ${ROMEO_USER}@${ROMEO_HOST}:${ROMEO_DEST}"
echo

# Cree le repertoire distant
ssh "${ROMEO_USER}@${ROMEO_HOST}" "mkdir -p '${ROMEO_DEST}'"

rsync -avz --progress \
    --exclude '.git' \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'Separation-Evaluation/obj' \
    --exclude 'Separation-Evaluation/bin' \
    --exclude 'Resultats/benchmarks/*.png' \
    --exclude 'Resultats/visualisations/*' \
    --exclude 'Resultats/solutions/*' \
    --exclude 'Resultats/logs/*' \
    "$RACINE/" "${ROMEO_USER}@${ROMEO_HOST}:${ROMEO_DEST}/"

echo
echo "Deploiement OK. Pour soumettre le job :"
echo "  ssh ${ROMEO_USER}@${ROMEO_HOST}"
echo "  cd ${ROMEO_DEST}"
echo "  sbatch Romeo/job_benchmark.sbatch"
echo
echo "Pour suivre :"
echo "  squeue -u ${ROMEO_USER}"
echo "  tail -f logs/bench_<JOB_ID>.out"
