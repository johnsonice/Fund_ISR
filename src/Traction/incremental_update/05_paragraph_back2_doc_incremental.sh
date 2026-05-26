#!/usr/bin/env bash
# Step 5: Aggregate topic-tagged paragraphs to document-by-type-topic level.
# Input:  paragraph_with_sector_incremental.csv (from step 04)
# Output: document_by_type_sector_incremental.csv
set -euo pipefail

cd /data/home/xiong/dev/Fund_ISR/src/Traction/
eval "$(conda shell.bash hook 2>/dev/null)" && conda activate traction 2>/dev/null || true

INCREMENTAL_DIR="/data/home/xiong/data/Fund/CSR/Tractions/output/incremental_update/05252026_update"

python paragraph_back2_doc.py \
  --input-csv "${INCREMENTAL_DIR}/paragraph_with_sector_incremental.csv" \
  --output-csv "${INCREMENTAL_DIR}/document_by_type_sector_incremental.csv" \
  --metafile "${INCREMENTAL_DIR}/IMF_Main_MetaData_20260525_filtered.xlsx"

echo "Done. Output: ${INCREMENTAL_DIR}/document_by_type_sector_incremental.csv"
