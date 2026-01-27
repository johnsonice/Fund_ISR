#!/bin/bash
# Prepare training data for all 4 task types
#
# Usage:
#   ./prepare_all_tasks.sh           # Run all tasks
#   ./prepare_all_tasks.sh --test    # Run in test mode (10 rows per task)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
TRAIN_EVAL_DIR="$PROJECT_ROOT/src/Traction/train_eval"

# Parse arguments
TEST_MODE=""
if [[ "$1" == "--test" ]]; then
    TEST_MODE="--test-mode"
    echo "Running in TEST MODE (10 rows per task)"
fi

# Activate conda environment
echo "Activating conda environment: traction"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate traction

# Task types to process
TASK_TYPES=(
    "monetary_stance"
    "fiscal_stance"
    "monetary_agreement"
    "fiscal_agreement"
)

echo "========================================"
echo "Preparing training data for all tasks"
echo "========================================"

for task in "${TASK_TYPES[@]}"; do
    echo ""
    echo "----------------------------------------"
    echo "Processing: $task"
    echo "----------------------------------------"
    python "$TRAIN_EVAL_DIR/prepare_data.py" --task-type "$task" $TEST_MODE
done

echo ""
echo "========================================"
echo "All tasks completed successfully!"
echo "========================================"
