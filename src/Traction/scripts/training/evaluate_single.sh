#!/bin/bash
# Evaluate a single fine-tuned model
#
# Usage:
#   ./evaluate_single.sh <task_type> <model_id>
#
# Example:
#   ./evaluate_single.sh monetary_stance ft:gpt-4.1-mini-2025-04-14:org::abc123

set -e

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <task_type> <model_id>"
    echo ""
    echo "Task types: monetary_stance, fiscal_stance, monetary_agreement, fiscal_agreement"
    echo ""
    echo "Example:"
    echo "  $0 monetary_stance ft:gpt-4.1-mini-2025-04-14:org::abc123"
    exit 1
fi

TASK_TYPE="$1"
MODEL_ID="$2"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
TRAIN_EVAL_DIR="$PROJECT_ROOT/src/Traction/train_eval"

# Activate conda environment
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate traction

echo "Task: $TASK_TYPE"
echo "Model: $MODEL_ID"
echo ""

python "$TRAIN_EVAL_DIR/evaluate.py" --task-type "$TASK_TYPE" --model-id "$MODEL_ID"
