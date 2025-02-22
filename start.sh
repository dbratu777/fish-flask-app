#!/usr/bin/env bash

_SCRIPT_DIR=$(dirname "$(realpath "$0")")

if command -v conda &>/dev/null; then
    source "$(conda info --base)/etc/profile.d/conda.sh"
else
    echo "ERROR: conda is not installed or not in the PATH."
    exit 1
fi

conda activate fish-flask-app                           || { echo "ERROR: failed to activate conda environment"; exit 1; }

trap 'conda deactivate' EXIT
cd "$_SCRIPT_DIR" || exit 1
$(conda run -n fish-flask-app which python) fishapp.py  || { echo "ERROR: failed to run fishapp.py"; exit 1; }

read -p "Press ENTER to exit..."