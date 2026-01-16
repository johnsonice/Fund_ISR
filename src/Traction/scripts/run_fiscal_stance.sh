# Run fiscal stance inference (test-mode) with the chosen prompt variant.
cd /data/home/xiong/dev/Fund_ISR/src/Traction/
conda activate traction
PROMPT_VARIANT=${PROMPT_VARIANT:-few_shot}

python inference_agreement_stance.py stance \
  --domain fiscal \
  --prompt-variant "$PROMPT_VARIANT" \
  --submit \
  --post-process \
  --model gpt-5 \
  --max-output-tokens 20000


# python inference_agreement_stance.py stance \
#   --domain fiscal \
#   --prompt-variant "$PROMPT_VARIANT" \
#   --submit \
#   --post-process \
#   --test-mode \
#   --model gpt-5 \
#   --sample-size 100 \
#   --max-output-tokens 20000

# python inference_agreement_stance.py stance \
#   --domain fiscal \
#   --prompt-variant "$PROMPT_VARIANT" \
#   --results-jsonl /data/home/xiong/data/Fund/CSR/Tractions/output/batch_695b5472d9bc819094bf41d987d0f3c0_output.jsonl \
#   --post-process \
#   --test-mode \
#   --sample-size 1000

