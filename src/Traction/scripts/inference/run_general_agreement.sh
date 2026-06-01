#!/usr/bin/env bash
# Run zero-shot general (cross-sector) agreement classification on the main dataset.
# This is the main-pipeline counterpart of
# `src/Traction/incremental_update/07_general_sentiment_incremental.sh`.
#
# Input:  ${MAIN_BASE_DIR}/df_documents.csv (copied from the archive snapshot
#         if missing — the adhoc regenerator is not invoked here; the archive's
#         file is the source of truth for the main-pipeline base).
# Output: ${MAIN_BASE_DIR}/df_documents_general.csv
set -euo pipefail

cd /data/home/xiong/dev/Fund_ISR/src/Traction/
eval "$(conda shell.bash hook 2>/dev/null)" && conda activate traction 2>/dev/null || true

# Pin the traction python so the script works even when conda activation no-ops
# (e.g. when invoked from another env in CI/agent contexts).
TRACTION_PY="${TRACTION_PY:-/data/home/xiong/miniconda3/envs/traction/bin/python}"
if [ ! -x "$TRACTION_PY" ]; then
  echo "ERROR: traction python not found at $TRACTION_PY" >&2
  echo "Set TRACTION_PY=/path/to/traction/bin/python or fix conda activation." >&2
  exit 1
fi

MAIN_BASE_DIR="${MAIN_BASE_DIR:-/data/home/xiong/data/Fund/CSR/Tractions/output/main_base}"
ARCHIVE_DF_DOCS="/data/home/xiong/data/Fund/CSR/Traction-archieve/output/df_documents.csv"
LIVE_DF_DOCS="${MAIN_BASE_DIR}/df_documents.csv"
OUTPUT_FILE="df_documents_general.csv"
MODEL=${MODEL:-gpt-5.4-mini}

mkdir -p "$MAIN_BASE_DIR"

# Copy df_documents.csv from the archive if it's not already in the main-base dir.
# cp -n is non-clobbering; force a fresh copy by `rm "$LIVE_DF_DOCS"` first.
if [ ! -f "$LIVE_DF_DOCS" ]; then
  echo "Copying df_documents.csv from archive: $ARCHIVE_DF_DOCS"
  cp -n "$ARCHIVE_DF_DOCS" "$LIVE_DF_DOCS"
else
  echo "df_documents.csv already present at $LIVE_DF_DOCS — skipping copy"
fi

echo "=== General Agreement (Zero-shot) — main pipeline ==="
"$TRACTION_PY" inference_general_agreement.py \
  --data-file "${LIVE_DF_DOCS}" \
  --output-dir "${MAIN_BASE_DIR}" \
  --output-file "${OUTPUT_FILE}" \
  --model "${MODEL}" \
  --prompt-variant simple \
  --submit \
  --post-process \
  --max-output-tokens 16384

echo "Done. Output: ${MAIN_BASE_DIR}/${OUTPUT_FILE}"
