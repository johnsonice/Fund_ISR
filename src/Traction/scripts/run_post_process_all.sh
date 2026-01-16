#!/usr/bin/env bash
# Post-process existing batch results for all 4 tasks (no submission).
set -euo pipefail

if [ "$#" -ne 4 ]; then
  echo "Usage: $(basename "$0") <monetary_agreement_jsonl> <monetary_stance_jsonl> <fiscal_agreement_jsonl> <fiscal_stance_jsonl>"
  exit 1
fi

cd /data/home/xiong/dev/Fund_ISR/src/Traction/
# conda activate traction
PROMPT_VARIANT=${PROMPT_VARIANT:-few_shot}

MONETARY_AGREEMENT_RESULTS="$1"
MONETARY_STANCE_RESULTS="$2"
FISCAL_AGREEMENT_RESULTS="$3"
FISCAL_STANCE_RESULTS="$4"

python inference_agreement_stance.py agreement \
  --domain monetary \
  --prompt-variant "$PROMPT_VARIANT" \
  --post-process \
  --results-jsonl "$MONETARY_AGREEMENT_RESULTS" \
  --model gpt-5 \
  --max-output-tokens 20000

python inference_agreement_stance.py stance \
  --domain monetary \
  --prompt-variant "$PROMPT_VARIANT" \
  --post-process \
  --results-jsonl "$MONETARY_STANCE_RESULTS" \
  --model gpt-5 \
  --max-output-tokens 20000

python inference_agreement_stance.py agreement \
  --domain fiscal \
  --prompt-variant "$PROMPT_VARIANT" \
  --post-process \
  --results-jsonl "$FISCAL_AGREEMENT_RESULTS" \
  --model gpt-5 \
  --max-output-tokens 20000

python inference_agreement_stance.py stance \
  --domain fiscal \
  --prompt-variant "$PROMPT_VARIANT" \
  --post-process \
  --results-jsonl "$FISCAL_STANCE_RESULTS" \
  --model gpt-5 \
  --max-output-tokens 20000

## how to use 
# bash /data/home/xiong/dev/Fund_ISR/src/Traction/scripts/run_post_process_all.sh \
#   /data/home/xiong/data/Fund/CSR/Tractions/output/batch_monetary_agreement_output.jsonl \
#   /data/home/xiong/data/Fund/CSR/Tractions/output/batch_monetary_stance_output.jsonl \
#   /data/home/xiong/data/Fund/CSR/Tractions/output/batch_fiscal_agreement_output.jsonl \
#   /data/home/xiong/data/Fund/CSR/Tractions/output/batch_fiscal_stance_output.jsonl