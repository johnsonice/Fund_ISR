#!/usr/bin/env bash
# Run monetary agreement inference with the chosen prompt variant.
set -euo pipefail

cd /data/home/xiong/dev/Fund_ISR/src/Traction/
eval "$(conda shell.bash hook 2>/dev/null)" && conda activate traction 2>/dev/null || true

# Pin the traction python so the script works even when conda activation
# silently no-ops (background processes, agent contexts).
TRACTION_PY="${TRACTION_PY:-/data/home/xiong/miniconda3/envs/traction/bin/python}"
if [ ! -x "$TRACTION_PY" ]; then
  echo "ERROR: traction python not found at $TRACTION_PY" >&2
  exit 1
fi

PROMPT_VARIANT=${PROMPT_VARIANT:-simple}
MAIN_BASE_DIR="${MAIN_BASE_DIR:-/data/home/xiong/data/Fund/CSR/Tractions/output/main_base}"

"$TRACTION_PY" inference_agreement_stance.py agreement \
  --domain monetary \
  --data-file "${MAIN_BASE_DIR}/document_by_type_sector.csv" \
  --output-dir "${MAIN_BASE_DIR}" \
  --prompt-variant "$PROMPT_VARIANT" \
  --submit \
  --post-process \
  --model ft:gpt-4.1-2025-04-14:protagolabs:monetary-agreement:D2McIjCy \
  --max-output-tokens 16384

# python inference_agreement_stance.py agreement \
#   --domain monetary \
#   --prompt-variant "$PROMPT_VARIANT" \
#   --submit \
#   --post-process \
#   --test-mode \
#   --sample-size 1000 \
#   --max-output-tokens 20000
