#!/usr/bin/env bash
# Ad-hoc: replicate the General Agreement v2 (zero-shot cross-sector) run into a
# fresh `general_agreement_v3/` folder for a reproducibility / model-randomness study.
#
# Background:
#   - The original v2 snapshot lives at
#     output/adhoc/general_agreement_v2/df_documents_general_v2.csv (981 rows).
#   - It was produced by `inference_general_agreement.py` with its DEFAULT params
#     (model=gpt-5.4-mini, prompt-variant=simple_v2, temperature=1.0,
#     max-output-tokens=16384) over input `main_base/df_documents.csv`.
#   - gpt-5.4-mini is a reasoning model: temperature is pinned to 1.0 and `seed`
#     is not supported, so the per-document integer scores are NOT bit-for-bit
#     reproducible. Two runs a week apart (2026-06-01 vs 2026-06-08) differed on
#     ~94% of the 981 documents. This run measures that randomness; it will NOT
#     reproduce the exact v2 numbers.
#
# Input:  main_base/df_documents.csv (same 981 docs the v2 snapshot used)
# Output: output/adhoc/general_agreement_v3/
#           - general_agreement_batch.jsonl        (batch request, 981 lines)
#           - batch_results_batch_*.jsonl          (raw batch responses)
#           - df_documents_general_v3.csv          (post-processed result, 981 rows)
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

OUTPUT_BASE="${OUTPUT_BASE:-/data/home/xiong/data/Fund/CSR/Tractions/output}"
DATA_FILE="${DATA_FILE:-${OUTPUT_BASE}/main_base/df_documents.csv}"
OUTPUT_DIR="${OUTPUT_DIR:-${OUTPUT_BASE}/adhoc/general_agreement_v3}"
OUTPUT_FILE="${OUTPUT_FILE:-df_documents_general_v3.csv}"

if [ ! -f "$DATA_FILE" ]; then
  echo "ERROR: input data file not found: $DATA_FILE" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "=== General Agreement v3 (replication of v2) ==="
echo "Input:  $DATA_FILE"
echo "Output: $OUTPUT_DIR/$OUTPUT_FILE"
echo "Config: model / prompt-variant simple_v2 / temperature 1.0 / max-output-tokens 16384 (script defaults = v2 recipe)"
echo

# All of model, prompt-variant (simple_v2), temperature (1.0) and
# max-output-tokens (16384) use inference_general_agreement.py's defaults,
# which ARE the v2 recipe. Do not pass them explicitly.
"$TRACTION_PY" inference_general_agreement.py \
  --data-file "${DATA_FILE}" \
  --output-dir "${OUTPUT_DIR}" \
  --output-file "${OUTPUT_FILE}" \
  --submit \
  --post-process

echo
echo "Done. Output: ${OUTPUT_DIR}/${OUTPUT_FILE}"
