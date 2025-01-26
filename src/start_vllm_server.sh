# Fixed values for server configuration
MODEL_PATH="/ephemeral/home/xiong/data/hf_cache/llama-3.1-8B-Instruct"
PORT=8000
TENSOR_PARALLEL_SIZE=1
SERVED_MODEL_NAME="llama-3.1-8b-Instruct"
GPU_DEVICE="6"
API_KEY="abc"

# Set GPU device and start server
export CUDA_VISIBLE_DEVICES=$GPU_DEVICE

python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --port "$PORT" \
    --tensor-parallel-size "$TENSOR_PARALLEL_SIZE" \
    --served-model_name "$SERVED_MODEL_NAME" \
    --trust-remote-code \
    --dtype bfloat16 \
    --api-key "$API_KEY"