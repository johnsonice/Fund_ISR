#!/usr/bin/env bash
# Step 6: Run agreement and stance inference on incremental data (4 batch jobs).
# Input:  document_by_type_sector_incremental.csv (from step 05)
# Output: agreement_monetary_results.csv, agreement_fiscal_results.csv,
#         stance_monetary_results.csv, stance_fiscal_results.csv
set -euo pipefail

cd /data/home/xiong/dev/Fund_ISR/src/Traction/
eval "$(conda shell.bash hook 2>/dev/null)" && conda activate traction 2>/dev/null || true

INCREMENTAL_DIR="/data/home/xiong/data/Fund/CSR/Tractions/output/incremental_update/05252026_update"
DATA_FILE="${INCREMENTAL_DIR}/document_by_type_sector_incremental.csv"
PROMPT_VARIANT=${PROMPT_VARIANT:-few_shot}

echo "=== Monetary Agreement ==="
python inference_agreement_stance.py agreement \
  --domain monetary \
  --data-file "${DATA_FILE}" \
  --output-dir "${INCREMENTAL_DIR}" \
  --model ft:gpt-4.1-2025-04-14:protagolabs:monetary-agreement:D2McIjCy \
  --prompt-variant "${PROMPT_VARIANT}" \
  --submit \
  --post-process \
  --max-output-tokens 16384

echo "=== Fiscal Agreement ==="
python inference_agreement_stance.py agreement \
  --domain fiscal \
  --data-file "${DATA_FILE}" \
  --output-dir "${INCREMENTAL_DIR}" \
  --model ft:gpt-4.1-2025-04-14:protagolabs:fiscal-agreement:D2O1nc5q \
  --prompt-variant "${PROMPT_VARIANT}" \
  --submit \
  --post-process \
  --max-output-tokens 16384

echo "=== Monetary Stance ==="
python inference_agreement_stance.py stance \
  --domain monetary \
  --data-file "${DATA_FILE}" \
  --output-dir "${INCREMENTAL_DIR}" \
  --model ft:gpt-4.1-2025-04-14:protagolabs:monetary-stance:D2K6qCDj \
  --prompt-variant "${PROMPT_VARIANT}" \
  --submit \
  --post-process \
  --max-output-tokens 16384

echo "=== Fiscal Stance ==="
python inference_agreement_stance.py stance \
  --domain fiscal \
  --data-file "${DATA_FILE}" \
  --output-dir "${INCREMENTAL_DIR}" \
  --model ft:gpt-4.1-2025-04-14:protagolabs:fiscal-stance:D2Lw2NJZ \
  --prompt-variant "${PROMPT_VARIANT}" \
  --submit \
  --post-process \
  --max-output-tokens 16384

echo "Done. All results in: ${INCREMENTAL_DIR}/"
