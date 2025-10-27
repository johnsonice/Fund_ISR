"""
Configuration file for GPT-5-mini fine-tuning pipeline.

Contains all paths, model settings, and hyperparameters for the monetary stance
classification fine-tuning workflow.
"""

import os
from pathlib import Path
from typing import List

# ============================================================================
# Data Paths
# ============================================================================

# Base data directory
DATA_DIR = Path("/data/home/xiong/data/Fund/CSR/Traction/output/finetuning/monetary/cv")

# Input Excel files
TRAINING_EXCEL = DATA_DIR / "training_2.xlsx"
TESTING_EXCEL = DATA_DIR / "testing_2.xlsx"

# Prompt template
PROJECT_ROOT = Path("/data/home/xiong/dev/Fund_ISR")
PROMPT_TEMPLATE_PATH = PROJECT_ROOT / "src/Traction/prompts/monetary_stance_simple.md"

# Output files
OUTPUT_DIR = DATA_DIR
TRAIN_JSONL = OUTPUT_DIR / "train.jsonl"
TEST_JSONL = OUTPUT_DIR / "test.jsonl"
DATA_STATS_JSON = OUTPUT_DIR / "data_stats.json"
FINETUNING_METADATA_JSON = OUTPUT_DIR / "finetuning_metadata.json"
EVALUATION_REPORT_MD =  "evaluation_report.md"
PREDICTIONS_CSV = OUTPUT_DIR / "predictions.csv"
METRICS_JSON = OUTPUT_DIR / "metrics.json"
PIPELINE_SUMMARY_MD = OUTPUT_DIR / "pipeline_summary.md"

# Log directory
LOG_DIR = PROJECT_ROOT / "src/Traction/log"

# ============================================================================
# Model Settings
# ============================================================================

# Base model for fine-tuning
# Using GPT-4.1-mini (April 2025 release)
BASE_MODEL = "gpt-4.1-mini-2025-04-14"

# Inference temperature (0 for deterministic outputs during evaluation)
TEMPERATURE = 0.0

# ============================================================================
# Fine-Tuning Hyperparameters
# ============================================================================

# Number of training epochs (default: 3, can be overridden)
# OpenAI may adjust this based on dataset size
N_EPOCHS = 3

# Batch size (set to "auto" to let OpenAI determine optimal size)
BATCH_SIZE = "auto"

# Learning rate multiplier (set to "auto" for OpenAI's recommendation)
# Range: 0.02 to 2.0 if specifying manually
LEARNING_RATE_MULTIPLIER = "auto"

# ============================================================================
# Data Processing Settings
# ============================================================================

# Excel column mappings
EXCEL_COLUMNS = {
    "country": "country",
    "year": "year",
    "staff_text": "staff",
    "buff_text": "buff",
    "staff_stance_current": "staff_stance_current",
    "staff_stance_future": "staff_stance_future",
    "buff_stance_current": "buff_stance_current",
    "buff_stance_future": "buff_stance_future",
}

# Text author labels (used in prompt template)
TEXT_AUTHOR_STAFF = "IMF staff"
TEXT_AUTHOR_AUTHORITY = "country authority"

# ============================================================================
# Label Definitions
# ============================================================================

# Current stance labels
STANCE_CURRENT_LABELS: List[str] = [
    "restrictive",
    "neutral",
    "accommodative",
    "unclear",
    "irrelevant"
]

# Future stance labels
STANCE_FUTURE_LABELS: List[str] = [
    "tightening",
    "tightening bias",
    "no change",
    "loosening bias",
    "loosening",
    "unclear",
    "irrelevant"
]

# ============================================================================
# API Settings
# ============================================================================

# Polling interval for monitoring fine-tuning job status (seconds)
JOB_POLL_INTERVAL = 60

# Retry settings for API calls
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # Exponential backoff multiplier

# ============================================================================
# Validation
# ============================================================================

def validate_paths():
    """Validate that required input files exist."""
    missing = []

    if not TRAINING_EXCEL.exists():
        missing.append(str(TRAINING_EXCEL))
    if not TESTING_EXCEL.exists():
        missing.append(str(TESTING_EXCEL))
    if not PROMPT_TEMPLATE_PATH.exists():
        missing.append(str(PROMPT_TEMPLATE_PATH))

    if missing:
        raise FileNotFoundError(
            f"Required input files not found:\n" + "\n".join(f"  - {p}" for p in missing)
        )

    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    return True


if __name__ == "__main__":
    # Test configuration
    print("Configuration Test")
    print("=" * 60)
    print(f"Training data: {TRAINING_EXCEL}")
    print(f"Testing data: {TESTING_EXCEL}")
    print(f"Prompt template: {PROMPT_TEMPLATE_PATH}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Base model: {BASE_MODEL}")
    print(f"N epochs: {N_EPOCHS}")
    print(f"\nModel Series: GPT-4.1-mini (April 2025)")
    print("\nValidating paths...")
    validate_paths()
    print("✓ All paths validated successfully!")
