# Run monetary agreement inference (test-mode) with the chosen prompt variant.
cd /data/home/xiong/dev/Fund_ISR/src/Traction/
conda activate traction
PROMPT_VARIANT=${PROMPT_VARIANT:-few_shot}

python inference_agreement_stance.py agreement \
  --domain monetary \
  --prompt-variant "$PROMPT_VARIANT" \
  --submit \
  --post-process \
  --model gpt-5 \
  --max-output-tokens 20000

# python inference_agreement_stance.py agreement \
#   --domain monetary \
#   --prompt-variant "$PROMPT_VARIANT" \
#   --submit \
#   --post-process \
#   --test-mode \
#   --sample-size 1000 \
#   --max-output-tokens 20000
