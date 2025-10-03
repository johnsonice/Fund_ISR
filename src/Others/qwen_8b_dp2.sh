
PORT=8080
API_KEY="SPRILA"
MODEL_PATH="/data/home/xiong/data/hf_cache/Qwen/Qwen3-8B"
SERVED_MODEL_NAME="Qwen/Qwen3-8B"
#GPU_DEVICE="0,1,3"
REASONING_PARSER="qwen3"

#TP_SIZE=2
#DP_SIZE=2


# Check if the specified PORT is already in use
if lsof -iTCP:$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "Error: Port $PORT is already in use. Please choose a different port or stop the process using it."
    exit 1
fi

# Set GPU device
#export CUDA_VISIBLE_DEVICES=$GPU_DEVICE
# Start SGLang server
python -m sglang.launch_server \
    --model-path "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port "$PORT" \
    --dtype bfloat16 \
    --api-key "$API_KEY" \
    --context-length 8192 \
    --served-model-name "$SERVED_MODEL_NAME" \
    --allow-auto-truncate \
    --constrained-json-whitespace-pattern "[\n\t ]*" \
    --reasoning-parser $REASONING_PARSER \
    #--dp-size $DP_SIZE \
    #--tp $TP_SIZE \
    #--mem-fraction-static 0.7 \