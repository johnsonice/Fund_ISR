"""
Shared utility functions for fine-tuning pipeline.

Contains helpers for logging, file I/O, API client setup, and validation.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from functools import wraps
import time

import pandas as pd
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging(log_dir: Path, script_name: str) -> logging.Logger:
    """
    Setup logging following existing pattern.

    Format: src/Traction/log/{USER}/{YYYY-MM-DD}/train_eval-{script}-{HH:MM}.log

    Args:
        log_dir: Base log directory (e.g., src/Traction/log)
        script_name: Name of the script (e.g., 'prepare_data', 'finetune')

    Returns:
        Configured logger instance
    """
    # Get username
    user = os.environ.get('USER', 'unknown')

    # Create directory structure: log/{USER}/{YYYY-MM-DD}
    today = datetime.now().strftime('%Y-%m-%d')
    log_subdir = log_dir / user / today
    log_subdir.mkdir(parents=True, exist_ok=True)

    # Log filename: train_eval-{script}-{HH:MM}.log
    timestamp = datetime.now().strftime('%H:%M')
    log_file = log_subdir / f"train_eval-{script_name}-{timestamp}.log"

    # Configure logger
    logger = logging.getLogger(f"train_eval.{script_name}")
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized: {log_file}")

    return logger


# ============================================================================
# OpenAI Client
# ============================================================================

def load_openai_client() -> OpenAI:
    """
    Load OpenAI client with API key from .env file.

    Returns:
        Initialized OpenAI client

    Raises:
        ValueError: If OPENAI_API_KEY not found in environment
    """
    # Load .env from project root
    env_path = PROJECT_ROOT / '.env'
    load_dotenv(env_path)

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError(
            f"OPENAI_API_KEY not found in environment. "
            f"Please set it in {env_path}"
        )

    return OpenAI(api_key=api_key)


# ============================================================================
# File I/O
# ============================================================================

def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """
    Read JSONL file into list of dictionaries.

    Args:
        file_path: Path to JSONL file

    Returns:
        List of dictionaries, one per line
    """
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line.strip()))
    return data


def save_jsonl(data: List[Dict[str, Any]], file_path: Path):
    """
    Write list of dictionaries to JSONL file.

    Args:
        data: List of dictionaries to write
        file_path: Output JSONL file path
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


def save_json(data: Dict[str, Any], file_path: Path, indent: int = 2):
    """
    Write dictionary to JSON file with pretty printing.

    Args:
        data: Dictionary to write
        file_path: Output JSON file path
        indent: Indentation level for pretty printing
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def load_json(file_path: Path) -> Dict[str, Any]:
    """
    Read JSON file into dictionary.

    Args:
        file_path: Path to JSON file

    Returns:
        Dictionary loaded from file
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================================
# Finetuning Dataset Validation
# ============================================================================
def check_finetuning_dataset(filepath):
    # Load the dataset
    with open(filepath, 'r', encoding='utf-8') as f:
        dataset = [json.loads(line) for line in f]

    # Initial dataset stats
    print("Num examples:", len(dataset))
    print("First example:")
    for message in dataset[-1]["messages"]:
        print(message)

    # Format error checks
    format_errors = defaultdict(int)

    for ex in dataset:
        if not isinstance(ex, dict):
            format_errors["data_type"] += 1
            continue

        messages = ex.get("messages", None)
        if not messages:
            format_errors["missing_messages_list"] += 1
            continue

        for message in messages:
            if "role" not in message or "content" not in message:
                format_errors["message_missing_key"] += 1

            if any(k not in (
            "role", "content", "name", "function_call", "weight") for k in
                   message):
                format_errors["message_unrecognized_key"] += 1

            if message.get("role", None) not in (
            "system", "user", "assistant", "function"):
                format_errors["unrecognized_role"] += 1

            content = message.get("content", None)
            function_call = message.get("function_call", None)

            if (not content and not function_call) or not isinstance(content,
                                                                     str):
                format_errors["missing_content"] += 1

        if not any(message.get("role", None) == "assistant" for message in
                   messages):
            format_errors["example_missing_assistant_message"] += 1

    if format_errors:
        print("Found errors:")
        for k, v in format_errors.items():
            print(f"{k}: {v}")
    else:
        print("No errors found")
        
# ============================================================================
# DataFrame Validation
# ============================================================================

def validate_dataframe(df: pd.DataFrame, required_cols: List[str]):
    """
    Validate DataFrame has required columns.

    Args:
        df: DataFrame to validate
        required_cols: List of required column names

    Raises:
        ValueError: If any required columns are missing
    """
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        raise ValueError(
            f"DataFrame missing required columns: {missing}\n"
            f"Available columns: {df.columns.tolist()}"
        )


# ============================================================================
# Prompt Template Utilities
# ============================================================================

def format_prompt_with_vars(template: str, variables: Dict[str, str]) -> str:
    """
    Replace {VARIABLE} placeholders in prompt template.

    Args:
        template: Template string with {VARIABLE} placeholders
        variables: Dictionary mapping variable names to values

    Returns:
        Formatted string with variables replaced

    Example:
        >>> template = "Country: {COUNTRY}; Year: {YEAR}"
        >>> variables = {"COUNTRY": "Thailand", "YEAR": "2016"}
        >>> format_prompt_with_vars(template, variables)
        'Country: Thailand; Year: 2016'
    """
    result = template
    for key, value in variables.items():
        placeholder = f"{{{key}}}"
        result = result.replace(placeholder, str(value))
    return result


# ============================================================================
# Label Validation
# ============================================================================

def validate_stance_labels(label: str, valid_labels: List[str]) -> bool:
    """
    Check if label is valid according to schema.

    Args:
        label: Label to validate
        valid_labels: List of valid label values

    Returns:
        True if valid, False otherwise
    """
    return label in valid_labels


# ============================================================================
# API Error Handling
# ============================================================================

def handle_api_error(max_retries: int = 3, backoff: float = 2.0):
    """
    Decorator for retry logic on OpenAI API calls.

    Args:
        max_retries: Maximum number of retry attempts
        backoff: Exponential backoff multiplier

    Example:
        @handle_api_error(max_retries=3)
        def make_api_call():
            return client.chat.completions.create(...)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    wait_time = backoff ** attempt
                    if attempt < max_retries - 1:
                        print(f"API error: {e}. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        print(f"API error after {max_retries} attempts: {e}")
                        raise
        return wrapper
    return decorator


# ============================================================================
# Directory Management
# ============================================================================

def create_output_dir(path: Path):
    """
    Create directory if it doesn't exist.

    Args:
        path: Directory path to create
    """
    path.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Evaluation Report
# ============================================================================

def write_evaluation_report(results: Dict, model_id: str, task_type: str, report_file: Path):
    """
    Write evaluation report to markdown.

    Args:
        results: Dict with metric names as keys, each containing accuracy/precision/recall/f1.
                 For stance tasks, includes '{field}_combined' keys for combined unclear/irrelevant.
        model_id: Fine-tuned model ID
        task_type: Task type (monetary_stance, fiscal_stance, etc.)
        report_file: Output path for markdown report
    """
    lines = [
        "# Evaluation Report",
        "",
        f"**Model**: `{model_id}`",
        f"**Task**: `{task_type}`",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Results",
        "",
    ]

    is_stance_task = 'stance' in task_type

    if is_stance_task:
        lines.extend([
            "| Field | Accuracy | F1 | Accuracy (combined) | F1 (combined) |",
            "|-------|----------|-----|---------------------|---------------|",
        ])
        for field in [f for f in results if not f.endswith('_combined')]:
            m = results[field]
            mc = results.get(f'{field}_combined', m)
            lines.append(f"| {field} | {m['accuracy']:.4f} | {m['f1']:.4f} | {mc['accuracy']:.4f} | {mc['f1']:.4f} |")
    else:
        lines.extend([
            "| Field | Accuracy | Precision | Recall | F1 |",
            "|-------|----------|-----------|--------|-----|",
        ])
        for field, m in results.items():
            lines.append(f"| {field} | {m['accuracy']:.4f} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1']:.4f} |")

    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text('\n'.join(lines))
    print(f"Report saved: {report_file}")


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    # Test utilities
    print("Testing utilities...")

    # Test logging
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)
        logger = setup_logging(log_dir, "test")
        logger.info("Test log message")
        print("✓ Logging works")

    # Test JSONL I/O
    test_data = [
        {"key1": "value1"},
        {"key2": "value2"}
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_file = Path(f.name)

    save_jsonl(test_data, temp_file)
    loaded_data = load_jsonl(temp_file)
    assert loaded_data == test_data
    temp_file.unlink()
    print("✓ JSONL I/O works")

    # Test prompt formatting
    template = "Country: {COUNTRY}; Year: {YEAR}"
    variables = {"COUNTRY": "Thailand", "YEAR": "2016"}
    result = format_prompt_with_vars(template, variables)
    assert result == "Country: Thailand; Year: 2016"
    print("✓ Prompt formatting works")

    # Test label validation
    valid_labels = ["restrictive", "neutral", "accommodative"]
    assert validate_stance_labels("neutral", valid_labels) == True
    assert validate_stance_labels("invalid", valid_labels) == False
    print("✓ Label validation works")

    print("\n✓ All utility tests passed!")
