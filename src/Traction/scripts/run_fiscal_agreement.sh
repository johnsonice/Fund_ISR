cd /data/home/xiong/dev/Fund_ISR/src/Traction/
PROMPT_VARIANT=${PROMPT_VARIANT:-few_shot}

# python inference_agreement_stance.py agreement \
#   --domain fiscal \
#   --prompt-variant "$PROMPT_VARIANT" \
#   --submit \
#   --post-process

python inference_agreement_stance.py agreement \
  --domain fiscal \
  --prompt-variant "$PROMPT_VARIANT" \
  --submit \
  --post-process \
  --test-mode \
  --sample-size 100