cd /data/home/xiong/dev/Fund_ISR/src/Traction/
PROMPT_VARIANT=${PROMPT_VARIANT:-chain_of_thought}

python inference_agreement_stance.py agreement \
  --domain fiscal \
  --prompt-variant "$PROMPT_VARIANT" \
  --submit \
  --post-process \
  --model gpt-5-nano 


# python inference_agreement_stance.py agreement \
#   --domain fiscal \
#   --prompt-variant "$PROMPT_VARIANT" \
#   --submit \
#   --post-process \
#   --test-mode \
#   --model gpt-5-nano \
#   --sample-size 1000