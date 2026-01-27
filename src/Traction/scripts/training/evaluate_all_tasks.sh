#!/bin/bash
# Evaluate fine-tuned GPT models for all 4 task types
# Prerequisite: Run finetune_all_tasks.sh first to train models

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
TRAIN_EVAL_DIR="$PROJECT_ROOT/src/Traction/train_eval"
DATA_BASE="/data/home/xiong/data/Fund/CSR/Tractions/Finetuning_data"

TASKS=(
    "monetary_stance"
    "fiscal_stance"
    "monetary_agreement"
    "fiscal_agreement"
)

# Map task to data directory
get_data_dir() {
    case "$1" in
        monetary_stance|monetary_agreement) echo "$DATA_BASE/Monetary/cv/jsonl" ;;
        fiscal_stance|fiscal_agreement) echo "$DATA_BASE/Fiscal/cv/jsonl" ;;
    esac
}

# Activate conda environment
echo "Activating conda environment: traction"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate traction

echo "========================================"
echo "Evaluating Fine-tuned Models"
echo "========================================"

for task in "${TASKS[@]}"; do
    echo ""
    echo "----------------------------------------"
    echo "Task: $task"
    echo "----------------------------------------"

    data_dir=$(get_data_dir "$task")
    metadata_file="$data_dir/finetuning_metadata_${task}.json"

    if [[ ! -f "$metadata_file" ]]; then
        echo "✗ Metadata file not found: $metadata_file"
        echo "  Run finetune_all_tasks.sh first"
        continue
    fi

    # Extract model ID from metadata JSON
    model_id=$(python -c "import json; print(json.load(open('$metadata_file'))['fine_tuned_model_id'])")

    if [[ -z "$model_id" || "$model_id" == "None" ]]; then
        echo "✗ No model ID found in metadata (fine-tuning may have failed)"
        continue
    fi

    echo "Model: $model_id"
    python "$TRAIN_EVAL_DIR/evaluate.py" --task-type "$task" --model-id "$model_id"
    echo "✓ $task completed"
done

echo ""
echo "========================================"
echo "All evaluations completed!"
echo "========================================"
