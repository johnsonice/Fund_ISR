#!/usr/bin/env bash
# Step 6: Run agreement and stance inference on incremental data (4 batch jobs).
# Input:  document_by_type_sector_incremental.csv (from step 05)
# Output: agreement_monetary_results.csv, agreement_fiscal_results.csv,
#         stance_monetary_results.csv, stance_fiscal_results.csv
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

INCREMENTAL_DIR="/data/home/xiong/data/Fund/CSR/Tractions/output/incremental_update/06_07_2026_update"
DATA_FILE="${INCREMENTAL_DIR}/document_by_type_sector_incremental.csv"
PROMPT_VARIANT=${PROMPT_VARIANT:-simple}

echo "=== Monetary Agreement ==="
"$TRACTION_PY" inference_agreement_stance.py agreement \
  --domain monetary \
  --data-file "${DATA_FILE}" \
  --output-dir "${INCREMENTAL_DIR}" \
  --model ft:gpt-4.1-2025-04-14:protagolabs:monetary-agreement:D2McIjCy \
  --prompt-variant "${PROMPT_VARIANT}" \
  --submit \
  --post-process \
  --max-output-tokens 16384

echo "=== Fiscal Agreement ==="
"$TRACTION_PY" inference_agreement_stance.py agreement \
  --domain fiscal \
  --data-file "${DATA_FILE}" \
  --output-dir "${INCREMENTAL_DIR}" \
  --model ft:gpt-4.1-2025-04-14:protagolabs:fiscal-agreement:D2O1nc5q \
  --prompt-variant "${PROMPT_VARIANT}" \
  --submit \
  --post-process \
  --max-output-tokens 16384

echo "=== Monetary Stance ==="
"$TRACTION_PY" inference_agreement_stance.py stance \
  --domain monetary \
  --data-file "${DATA_FILE}" \
  --output-dir "${INCREMENTAL_DIR}" \
  --model ft:gpt-4.1-2025-04-14:protagolabs:monetary-stance:D2K6qCDj \
  --prompt-variant "${PROMPT_VARIANT}" \
  --submit \
  --post-process \
  --max-output-tokens 16384

echo "=== Fiscal Stance ==="
"$TRACTION_PY" inference_agreement_stance.py stance \
  --domain fiscal \
  --data-file "${DATA_FILE}" \
  --output-dir "${INCREMENTAL_DIR}" \
  --model ft:gpt-4.1-2025-04-14:protagolabs:fiscal-stance:D2Lw2NJZ \
  --prompt-variant "${PROMPT_VARIANT}" \
  --submit \
  --post-process \
  --max-output-tokens 16384

echo "Done. All results in: ${INCREMENTAL_DIR}/"
