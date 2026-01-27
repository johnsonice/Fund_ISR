#!/bin/bash
# Fine-tune GPT models for all 4 task types
# Prerequisite: Run prepare_all_tasks.sh first to generate training data

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
TRAIN_EVAL_DIR="$PROJECT_ROOT/src/Traction/train_eval"

TASKS=(
    "monetary_stance"
    "fiscal_stance"
    "monetary_agreement"
    "fiscal_agreement"
)

# Activate conda environment
echo "Activating conda environment: traction"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate traction

echo "========================================"
echo "Fine-tuning GPT for All Tasks"
echo "========================================"

for task in "${TASKS[@]}"; do
    echo ""
    echo "----------------------------------------"
    echo "Task: $task"
    echo "----------------------------------------"
    python "$TRAIN_EVAL_DIR/finetune.py" --task-type "$task" --model gpt-4.1-2025-04-14 #gpt-4.1-mini-2025-04-14
    echo "✓ $task completed"
done

echo ""
echo "========================================"
echo "All tasks completed!"
echo "========================================"
