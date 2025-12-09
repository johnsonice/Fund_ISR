cd /data/home/xiong/dev/Fund_ISR/src/Traction/
PROMPT_VARIANT=${PROMPT_VARIANT:-few_shot}
#python inference_agreement_stance.py agreement --domain fiscal  --test-mode --sample-size 100 --prompt-variant "$PROMPT_VARIANT"
python inference_agreement_stance.py agreement \
  --domain monetary \
  --prompt-variant "$PROMPT_VARIANT" \
  --submit \
  --post-process

python inference_agreement_stance.py agreement \
  --domain monetary \
  --prompt-variant "$PROMPT_VARIANT" \
  --submit \
  --post-process \
  --test-mode \
  --sample-size 100
