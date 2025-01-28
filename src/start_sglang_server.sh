#!/bin/bash

# Fixed values for server configuration
MODEL_PATH="/ephemeral/home/xiong/data/hf_cache/llama-3.1-8B-Instruct"
PORT=8000
API_KEY="abc"
SERVED_MODEL_NAME="llama-3.1-8b-Instruct"
GPU_DEVICE="4,5,6,7"
DP_SIZE=4
# Set GPU device
export CUDA_VISIBLE_DEVICES=$GPU_DEVICE

# Start SGLang server
python -m sglang.launch_server \
    --model "$MODEL_PATH" \
    --port "$PORT" \
    --dtype bfloat16 \
    --api-key "$API_KEY" \
    --context-length 8192 \
    --served-model-name "$SERVED_MODEL_NAME" \
    --allow-auto-truncate \
    --dp-size $DP_SIZE
