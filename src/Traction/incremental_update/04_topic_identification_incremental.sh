#!/usr/bin/env bash
# Step 4: Run topic identification on incremental paragraphs via OpenAI Batch API.
# Input:  df_paragraphs_incremental.csv (from step 03)
# Output: paragraph_with_sector_incremental.csv (with topic scores and dummies)
set -euo pipefail

cd /data/home/xiong/dev/Fund_ISR/src/Traction/
eval "$(conda shell.bash hook 2>/dev/null)" && conda activate traction 2>/dev/null || true

INCREMENTAL_DIR="/data/home/xiong/data/Fund/CSR/Tractions/output/incremental_update/05252026_update"

python topic_identification_batch.py \
  --input_file df_paragraphs_incremental.csv \
  --output-dir "${INCREMENTAL_DIR}" \
  --output_file paragraph_with_sector_incremental.csv \
  --jsonl-file topic_identification_incremental_batch.jsonl \
  --create-batch \
  --submit \
  --post-process \
  --model gpt-5.4-mini

echo "Done. Output: ${INCREMENTAL_DIR}/paragraph_with_sector_incremental.csv"
