#!/usr/bin/env bash
# Build the main-pipeline final dataset (df_fin.csv + df_fin_reg_core.csv) from
# the refreshed inference outputs in /output/.
set -euo pipefail

cd /data/home/xiong/dev/Fund_ISR/src/Traction/
eval "$(conda shell.bash hook 2>/dev/null)" && conda activate traction 2>/dev/null || true

TRACTION_PY="${TRACTION_PY:-/data/home/xiong/miniconda3/envs/traction/bin/python}"
if [ ! -x "$TRACTION_PY" ]; then
  echo "ERROR: traction python not found at $TRACTION_PY" >&2
  exit 1
fi

"$TRACTION_PY" create_final_dataset.py "$@"
