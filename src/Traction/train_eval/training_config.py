"""
Configuration file for GPT fine-tuning pipeline.

Contains all paths, model settings, and hyperparameters for the stance and
agreement classification fine-tuning workflow. Supports all four task types:
- monetary_stance
- fiscal_stance
- monetary_agreement
- fiscal_agreement
"""

from pathlib import Path
from typing import List, Dict, Any

# ============================================================================
# Project Paths
# ============================================================================

PROJECT_ROOT = Path("/data/home/xiong/dev/Fund_ISR")
PROMPTS_DIR = PROJECT_ROOT / "src/Traction/prompts"
LOG_DIR = PROJECT_ROOT / "src/Traction/log"

# ============================================================================
# Task Types
# ============================================================================

TASK_TYPES = ['monetary_stance', 'fiscal_stance', 'monetary_agreement', 'fiscal_agreement']
DEFAULT_TASK_TYPE = 'monetary_stance'

# ============================================================================
# Data Paths by Task Type
# ============================================================================

# Base data directory per task
DATA_DIRS = {
    'monetary_stance': Path("/data/home/xiong/data/Fund/CSR/Tractions/Finetuning_data/Monetary/cv"),
    'fiscal_stance': Path("/data/home/xiong/data/Fund/CSR/Tractions/Finetuning_data/Fiscal/cv"),
    'monetary_agreement': Path("/data/home/xiong/data/Fund/CSR/Tractions/Finetuning_data/Monetary/cv"),
    'fiscal_agreement': Path("/data/home/xiong/data/Fund/CSR/Tractions/Finetuning_data/Fiscal/cv"),
}

# Default data directory (for backward compatibility)
DATA_DIR = DATA_DIRS[DEFAULT_TASK_TYPE]

# # Input Excel files (default for backward compatibility)
# TRAINING_EXCEL = DATA_DIR / "training_0.xlsx"
# TESTING_EXCEL = DATA_DIR / "testing_0.xlsx"

# Prompt template paths per task type
PROMPT_TEMPLATE_PATHS = {
    'monetary_stance': PROMPTS_DIR / "monetary_stance_simple.md",
    'fiscal_stance': PROMPTS_DIR / "fiscal_stance_simple.md",
    'monetary_agreement': PROMPTS_DIR / "monetary_agreement_simple.md",
    'fiscal_agreement': PROMPTS_DIR / "fiscal_agreement_simple.md",
}
# Default prompt template path (for backward compatibility)
PROMPT_TEMPLATE_PATH = PROMPT_TEMPLATE_PATHS[DEFAULT_TASK_TYPE]

# Output files (default directory)
OUTPUT_DIR = DATA_DIR
TRAIN_JSONL = OUTPUT_DIR / "train.jsonl"
TEST_JSONL = OUTPUT_DIR / "test.jsonl"
DATA_STATS_JSON = OUTPUT_DIR / "data_stats.json"
FINETUNING_METADATA_JSON = OUTPUT_DIR / "finetuning_metadata.json"
EVALUATION_REPORT_MD = "evaluation_report.md"
PREDICTIONS_CSV = OUTPUT_DIR / "predictions.csv"
METRICS_JSON = OUTPUT_DIR / "metrics.json"
PIPELINE_SUMMARY_MD = OUTPUT_DIR / "pipeline_summary.md"

# ============================================================================
# Model Settings
# ============================================================================

# Base model for fine-tuning
# Using GPT-4.1-mini (April 2025 release)
BASE_MODEL = "gpt-4.1-mini-2025-04-14"
# Inference temperature (0 for deterministic outputs during evaluation)
TEMPERATURE = 0.0
# Random seed for reproducible inference (used with temperature=0)
SEED = 42
# Number of training epochs (default: 3, can be overridden)
# OpenAI may adjust this based on dataset size
N_EPOCHS = 3
BATCH_SIZE = "auto"
# Learning rate multiplier (set to "auto" for OpenAI's recommendation)
# Range: 0.02 to 2.0 if specifying manually
LEARNING_RATE_MULTIPLIER = "auto"

# Excel column mappings (default for backward compatibility - monetary_stance)
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

# Task-specific Excel column mappings
TASK_EXCEL_COLUMNS: Dict[str, Dict[str, str]] = {
    'monetary_stance': {
        "country": "country",
        "year": "year",
        "staff_text": "staff",
        "buff_text": "buff",
        "staff_stance_current": "staff_stance_current",
        "staff_stance_future": "staff_stance_future",
        "buff_stance_current": "buff_stance_current",
        "buff_stance_future": "buff_stance_future",
    },
    'fiscal_stance': {
        "country": "country",
        "year": "year",
        "staff_text": "staff",
        "buff_text": "buff",
        "staff_stance_near_term": "staff_stance_near_term",
        "buff_stance_near_term": "buff_stance_near_term",
    },
    'monetary_agreement': {
        "country": "country",
        "year": "year",
        "staff_text": "staff",
        "buff_text": "buff",
        "agreement": "agreement_general",
        "disagreement_areas": "disagreement_areas",
    },
    'fiscal_agreement': {
        "country": "country",
        "year": "year",
        "staff_text": "staff",
        "buff_text": "buff",
        "agreement": "agreement_general",
        "disagreement_areas": "disagreement_areas",
    },
}

# Text author labels (used in prompt template)
TEXT_AUTHOR_STAFF = "IMF staff"
TEXT_AUTHOR_AUTHORITY = "country authority"

# ============================================================================
# Label Definitions
# ============================================================================

# Current stance labels (monetary)
STANCE_CURRENT_LABELS: List[str] = [
    "restrictive",
    "neutral",
    "accommodative",
    "unclear",
    "irrelevant"
]

# Future stance labels (monetary and fiscal)
STANCE_FUTURE_LABELS: List[str] = [
    "tightening",
    "tightening bias",
    "no change",
    "loosening bias",
    "loosening",
    "unclear",
    "irrelevant"
]

# Agreement labels
AGREEMENT_LABELS: List[str] = [
    "irrelevant",
    "disagreement exists",
    "mostly agree"
]

# Task-specific label definitions
TASK_LABELS: Dict[str, Dict[str, List[str]]] = {
    'monetary_stance': {
        'stance_current': STANCE_CURRENT_LABELS,
        'stance_future': STANCE_FUTURE_LABELS,
    },
    'fiscal_stance': {
        'stance_near_term': STANCE_FUTURE_LABELS,
    },
    'monetary_agreement': {
        'agreement': AGREEMENT_LABELS,
    },
    'fiscal_agreement': {
        'agreement': AGREEMENT_LABELS,
    },
}

# Output fields per task type
TASK_OUTPUT_FIELDS: Dict[str, List[str]] = {
    'monetary_stance': ['stance_current', 'stance_future'],
    'fiscal_stance': ['stance_near_term'],
    'monetary_agreement': ['agreement', 'disagreement_areas'],
    'fiscal_agreement': ['agreement', 'disagreement_areas'],
}

# ============================================================================
# API Settings
# ============================================================================

# Polling interval for monitoring fine-tuning job status (seconds)
JOB_POLL_INTERVAL = 60
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # Exponential backoff multiplier

# ============================================================================
# Helper Functions
# ============================================================================

def get_task_config(task_type: str) -> Dict[str, Any]:
    """
    Get configuration for a specific task type.

    Args:
        task_type: One of TASK_TYPES

    Returns:
        Dictionary with task-specific configuration
    """
    if task_type not in TASK_TYPES:
        raise ValueError(f"Invalid task type: {task_type}. Must be one of {TASK_TYPES}")

    data_dir = DATA_DIRS[task_type]
    return {
        'task_type': task_type,
        'data_dir': data_dir,
        'training_excel': data_dir / "training_0.xlsx",
        'testing_excel': data_dir / "testing_0.xlsx",
        'prompt_template': PROMPT_TEMPLATE_PATHS[task_type],
        'output_dir': data_dir / "jsonl",
        'excel_columns': TASK_EXCEL_COLUMNS[task_type],
        'labels': TASK_LABELS[task_type],
        'output_fields': TASK_OUTPUT_FIELDS[task_type],
    }


def get_required_columns(task_type: str) -> List[str]:
    """
    Get required DataFrame columns for a specific task type.

    Args:
        task_type: One of TASK_TYPES

    Returns:
        List of required column names
    """
    cols = TASK_EXCEL_COLUMNS[task_type]
    return list(cols.values())

# ============================================================================
# Validation
# ============================================================================

def validate_paths(task_type: str = DEFAULT_TASK_TYPE):
    """
    Validate that required input files exist for a task type.

    Args:
        task_type: Task type to validate paths for
    """
    config = get_task_config(task_type)
    missing = []

    if not config['training_excel'].exists():
        missing.append(str(config['training_excel']))
    if not config['testing_excel'].exists():
        missing.append(str(config['testing_excel']))
    if not config['prompt_template'].exists():
        missing.append(str(config['prompt_template']))

    if missing:
        raise FileNotFoundError(
            f"Required input files not found for task '{task_type}':\n" +
            "\n".join(f"  - {p}" for p in missing)
        )

    # Create output directory if it doesn't exist
    config['output_dir'].mkdir(parents=True, exist_ok=True)

    return True


if __name__ == "__main__":
    # Test configuration
    print("Configuration Test")
    print("=" * 60)
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Prompts directory: {PROMPTS_DIR}")
    print(f"Base model: {BASE_MODEL}")
    print(f"N epochs: {N_EPOCHS}")
    print(f"\nModel Series: GPT-4.1-mini (April 2025)")

    print("\n" + "=" * 60)
    print("Available task types:")
    for task_type in TASK_TYPES:
        config = get_task_config(task_type)
        print(f"\n  {task_type}:")
        print(f"    Data dir: {config['data_dir']}")
        print(f"    Prompt: {config['prompt_template'].name}")
        print(f"    Output fields: {config['output_fields']}")

    print("\n" + "=" * 60)
    print("Validating prompt templates...")
    for task_type, prompt_path in PROMPT_TEMPLATE_PATHS.items():
        if prompt_path.exists():
            print(f"  ✓ {task_type}: {prompt_path.name}")
        else:
            print(f"  ✗ {task_type}: {prompt_path.name} NOT FOUND")

    print("\n✓ Configuration loaded successfully!")
