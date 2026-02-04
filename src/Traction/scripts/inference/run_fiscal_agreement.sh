# Run fiscal agreement inference (test-mode) with the chosen prompt variant.
cd /data/home/xiong/dev/Fund_ISR/src/Traction/
eval "$(conda shell.bash hook)" && conda activate traction
PROMPT_VARIANT=${PROMPT_VARIANT:-few_shot}

python inference_agreement_stance.py agreement \
  --domain fiscal \
  --prompt-variant "$PROMPT_VARIANT" \
  --submit \
  --post-process \
  --model ft:gpt-4.1-2025-04-14:protagolabs:fiscal-agreement:D2O1nc5q \
  --max-output-tokens 16384

# python inference_agreement_stance.py agreement \
#   --domain fiscal \
#   --prompt-variant "$PROMPT_VARIANT" \
#   --submit \
#   --post-process \
#   --test-mode \
#   --model gpt-5 \
#   --sample-size 1000 \
#   --max-output-tokens 20000