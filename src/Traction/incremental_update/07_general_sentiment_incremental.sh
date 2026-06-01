#!/usr/bin/env bash
# Step 7: Zero-shot general (cross-sector) agreement classification on incremental docs.
# Input:  df_documents_incremental.csv (one row per doc; staff/buff/country/year columns)
# Output: df_documents_general_incremental.csv
set -euo pipefail

cd /data/home/xiong/dev/Fund_ISR/src/Traction/
eval "$(conda shell.bash hook 2>/dev/null)" && conda activate traction 2>/dev/null || true

# Resolve traction env's python explicitly — `conda activate traction` above can
# silently no-op when the parent shell already has another env active (e.g. in
# agent/CI contexts), and the rest of this pipeline depends on traction-only
# packages (frontmatter, openai SDK pinned version, etc).
TRACTION_PY="${TRACTION_PY:-/data/home/xiong/miniconda3/envs/traction/bin/python}"
if [ ! -x "$TRACTION_PY" ]; then
  echo "ERROR: traction python not found at $TRACTION_PY" >&2
  echo "Set TRACTION_PY=/path/to/traction/bin/python or fix conda activation." >&2
  exit 1
fi

INCREMENTAL_DIR="/data/home/xiong/data/Fund/CSR/Tractions/output/incremental_update/05252026_update"
DATA_FILE="${INCREMENTAL_DIR}/df_documents_incremental.csv"
OUTPUT_FILE="df_documents_general_incremental.csv"
MODEL=${MODEL:-gpt-5.4-mini}

echo "=== General Agreement (Zero-shot) ==="
"$TRACTION_PY" inference_general_agreement.py \
  --data-file "${DATA_FILE}" \
  --output-dir "${INCREMENTAL_DIR}" \
  --output-file "${OUTPUT_FILE}" \
  --model "${MODEL}" \
  --prompt-variant simple \
  --submit \
  --post-process \
  --max-output-tokens 16384

echo "Done. Output: ${INCREMENTAL_DIR}/df_documents_general_incremental.csv"
