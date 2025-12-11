cd /data/home/xiong/dev/Fund_ISR/src/Traction/
PROMPT_VARIANT=${PROMPT_VARIANT:-few_shot}

python inference_agreement_stance.py stance \
  --domain monetary \
  --prompt-variant "$PROMPT_VARIANT" \
  --submit \
  --post-process \
  --model gpt-5-nano 


# python inference_agreement_stance.py stance \
#   --domain monetary \
#   --prompt-variant "$PROMPT_VARIANT" \
#   --submit \
#   --post-process \
#   --test-mode \
#   --sample-size 100
