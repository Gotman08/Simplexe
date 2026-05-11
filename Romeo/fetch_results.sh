#!/usr/bin/env bash
# Recupere les resultats du benchmark depuis Romeo
#
# Usage : bash Romeo/fetch_results.sh

set -euo pipefail

cd "$(dirname "$0")/.."

ROMEO_USER="${ROMEO_USER:-$USER}"
ROMEO_HOST="${ROMEO_HOST:-romeo.univ-reims.fr}"
ROMEO_DEST="${ROMEO_DEST:-/home/$ROMEO_USER/chps0805}"

echo "Recuperation des resultats depuis ${ROMEO_USER}@${ROMEO_HOST}:${ROMEO_DEST}/Resultats/"

mkdir -p Resultats
rsync -avz --progress \
    "${ROMEO_USER}@${ROMEO_HOST}:${ROMEO_DEST}/Resultats/" Resultats_romeo/

echo
echo "Termine. Resultats Romeo dans : Resultats_romeo/"
