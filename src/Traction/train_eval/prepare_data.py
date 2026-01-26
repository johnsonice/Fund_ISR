"""
Data preparation script for GPT-5-mini fine-tuning.

Converts Excel data to OpenAI JSONL format for monetary stance classification.
Creates dual examples (staff + authority) from each row.
"""
#%%
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import Counter

import pandas as pd
from tqdm import tqdm

# Add project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "libs"))

from libs.prompt_utils import load_prompt
import training_config as config
from training_utils import (
    setup_logging,
    validate_dataframe,
    save_jsonl,
    save_json,
    format_prompt_with_vars,
    validate_stance_labels,
)
#%%

# ============================================================================
# Data Loading
# ============================================================================

def load_excel_data(file_path: Path, logger) -> pd.DataFrame:
    """
    Load and validate Excel file structure.

    Args:
        file_path: Path to Excel file
        logger: Logger instance

    Returns:
        Loaded DataFrame
    """
    logger.info(f"Loading data from: {file_path}")
    df = pd.read_excel(file_path)

    logger.info(f"Loaded {len(df)} rows")
    # Validate required columns
    required_cols = list(config.EXCEL_COLUMNS.values())
    validate_dataframe(df, required_cols)

    return df


def load_prompt_template(template_path: Path, logger) -> Dict[str, str]:
    """
    Load monetary_stance_simple.md using libs/prompt_utils.py.
    Args:
        template_path: Path to prompt markdown file
        logger: Logger instance
    Returns:
        Dictionary with 'system', 'user', 'schema' sections
    """
    logger.info(f"Loading prompt template from: {template_path}")
    prompt = load_prompt(template_path)
    sections = prompt.sections # Extract sections
    return sections


# ============================================================================
# Example Creation
# ============================================================================

def create_training_example(
    row: pd.Series,
    text_col: str,
    text_author: str,
    label_current_col: str,
    label_future_col: str,
    prompt_sections: Dict[str, str],
    logger,
) -> Dict[str, Any]:
    """
    Create single OpenAI message format example.

    Args:
        row: DataFrame row
        text_col: Column name for text (e.g., 'staff' or 'buff')
        text_author: Author description for prompt (e.g., 'IMF staff')
        label_current_col: Column for current stance label
        label_future_col: Column for future stance label
        prompt_sections: Prompt template sections
        logger: Logger instance

    Returns:
        Dictionary in OpenAI messages format:
        {
            "messages": [
                {"role": "system", "content": "..."},
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": '{"stance_current": "...", "stance_future": "..."}'}
            ]
        }
    """
    # Extract values
    country = row[config.EXCEL_COLUMNS['country']]
    year = row[config.EXCEL_COLUMNS['year']]
    text = row[text_col]
    stance_current = row[label_current_col]
    stance_future = row[label_future_col]

    # Skip if text is missing or NaN
    if pd.isna(text) or not text or len(str(text).strip()) == 0:
        return None

    # Skip if labels are missing
    if pd.isna(stance_current) or pd.isna(stance_future):
        return None

    # Validate labels
    if not validate_stance_labels(stance_current, config.STANCE_CURRENT_LABELS):
        logger.warning(
            f"Invalid current stance label '{stance_current}' for {country} {year}, skipping"
        )
        return None

    if not validate_stance_labels(stance_future, config.STANCE_FUTURE_LABELS):
        logger.warning(
            f"Invalid future stance label '{stance_future}' for {country} {year}, skipping"
        )
        return None

    # Format system message with TEXT_AUTHOR variable
    system_content = format_prompt_with_vars(
        prompt_sections['system'],
        {"TEXT_AUTHOR": text_author}
    )

    # Format user message with COUNTRY, YEAR, TEXT variables
    user_content = format_prompt_with_vars(
        prompt_sections['user'],
        {
            "COUNTRY": str(country),
            "YEAR": str(year),
            "TEXT": str(text).strip()
        }
    )

    # Create assistant response as JSON string
    assistant_content = json.dumps({
        "stance_current": stance_current,
        "stance_future": stance_future
    })

    # Construct messages
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
        {"role": "assistant", "content": assistant_content}
    ]

    return {"messages": messages}


def prepare_dataset(
    df: pd.DataFrame,
    prompt_sections: Dict[str, str],
    logger,
) -> List[Dict[str, Any]]:
    """
    Generate examples for both staff and authority from each row.

    Creates dual examples:
    - One using 'staff' text with staff labels
    - One using 'buff' text with buff labels

    Args:
        df: Input DataFrame
        prompt_sections: Prompt template sections
        logger: Logger instance

    Returns:
        List of training examples in OpenAI format
    """
    examples = []

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing rows"):
        # Create staff example
        staff_example = create_training_example(
            row=row,
            text_col=config.EXCEL_COLUMNS['staff_text'],
            text_author=config.TEXT_AUTHOR_STAFF,
            label_current_col=config.EXCEL_COLUMNS['staff_stance_current'],
            label_future_col=config.EXCEL_COLUMNS['staff_stance_future'],
            prompt_sections=prompt_sections,
            logger=logger,
        )

        if staff_example:
            examples.append(staff_example)

        # Create authority example
        buff_example = create_training_example(
            row=row,
            text_col=config.EXCEL_COLUMNS['buff_text'],
            text_author=config.TEXT_AUTHOR_AUTHORITY,
            label_current_col=config.EXCEL_COLUMNS['buff_stance_current'],
            label_future_col=config.EXCEL_COLUMNS['buff_stance_future'],
            prompt_sections=prompt_sections,
            logger=logger,
        )

        if buff_example:
            examples.append(buff_example)

    return examples


# ============================================================================
# Statistics
# ============================================================================

def generate_stats_report(
    train_examples: List[Dict[str, Any]],
    test_examples: List[Dict[str, Any]],
    logger,
) -> Dict[str, Any]:
    """
    Calculate and save dataset statistics.

    Args:
        train_examples: Training examples
        test_examples: Test examples
        logger: Logger instance

    Returns:
        Statistics dictionary
    """
    def extract_labels(examples):
        """Extract stance labels from examples."""
        current_labels = []
        future_labels = []

        for ex in examples:
            assistant_msg = ex['messages'][2]['content']  # Assistant message
            labels = json.loads(assistant_msg)
            current_labels.append(labels['stance_current'])
            future_labels.append(labels['stance_future'])

        return current_labels, future_labels

    def calculate_text_stats(examples):
        """Calculate text length statistics."""
        lengths = []
        for ex in examples:
            user_msg = ex['messages'][1]['content']  # User message
            lengths.append(len(user_msg))
        return {
            'mean': sum(lengths) / len(lengths) if lengths else 0,
            'min': min(lengths) if lengths else 0,
            'max': max(lengths) if lengths else 0
        }

    # Extract labels
    train_current, train_future = extract_labels(train_examples)
    test_current, test_future = extract_labels(test_examples)

    # Count labels
    stats = {
        'dataset_size': {
            'train': len(train_examples),
            'test': len(test_examples),
            'total': len(train_examples) + len(test_examples)
        },
        'label_distributions': {
            'train': {
                'stance_current': dict(Counter(train_current)),
                'stance_future': dict(Counter(train_future))
            },
            'test': {
                'stance_current': dict(Counter(test_current)),
                'stance_future': dict(Counter(test_future))
            }
        },
        'text_length': {
            'train': calculate_text_stats(train_examples),
            'test': calculate_text_stats(test_examples)
        }
    }

    return stats

# ============================================================================
# Argument Parsing & Validation
# ============================================================================
def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for data preparation script.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Prepare JSONL data for fine-tuning (train/test + stats)."
    )
    parser.add_argument(
        "--training-excel",
        type=Path,
        default=config.TRAINING_EXCEL,
        help="Path to training Excel file",
    )
    parser.add_argument(
        "--testing-excel",
        type=Path,
        default=config.TESTING_EXCEL,
        help="Path to testing Excel file",
    )
    parser.add_argument(
        "--prompt-template",
        type=Path,
        default=config.PROMPT_TEMPLATE_PATH,
        help="Path to prompt template markdown file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=config.OUTPUT_DIR,
        help="Output directory for JSONL and stats files",
    )
    parser.add_argument(
        "--train-jsonl",
        type=Path,
        default=None,
        help="Output path for training JSONL (defaults to output dir)",
    )
    parser.add_argument(
        "--test-jsonl",
        type=Path,
        default=None,
        help="Output path for testing JSONL (defaults to output dir)",
    )
    parser.add_argument(
        "--data-stats-json",
        type=Path,
        default=None,
        help="Output path for dataset statistics JSON (defaults to output dir)",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=config.LOG_DIR,
        help="Log directory",
    )

    return parser.parse_args()


def resolve_output_paths(args: argparse.Namespace) -> Tuple[Path, Path, Path, Path]:
    """
    Resolve output paths based on CLI args and defaults.

    Returns:
        output_dir, train_jsonl, test_jsonl, data_stats_json
    """
    output_dir = args.output_dir
    train_jsonl = args.train_jsonl or (output_dir / "train.jsonl")
    test_jsonl = args.test_jsonl or (output_dir / "test.jsonl")
    data_stats_json = args.data_stats_json or (output_dir / "data_stats.json")

    return output_dir, train_jsonl, test_jsonl, data_stats_json


def validate_paths(
    training_excel: Path,
    testing_excel: Path,
    prompt_template: Path,
    output_dir: Path,
):
    """Validate required inputs and ensure output directory exists."""
    missing = []
    if not training_excel.exists():
        missing.append(str(training_excel))
    if not testing_excel.exists():
        missing.append(str(testing_excel))
    if not prompt_template.exists():
        missing.append(str(prompt_template))

    if missing:
        raise FileNotFoundError(
            "Required input files not found:\n" + "\n".join(f"  - {p}" for p in missing)
        )

    output_dir.mkdir(parents=True, exist_ok=True)

#%%
# ============================================================================
# Main Pipeline
# ============================================================================

def main():
    """Main execution pipeline."""
    args = parse_arguments()
    output_dir, train_jsonl, test_jsonl, data_stats_json = resolve_output_paths(args)

    # Setup logging
    logger = setup_logging(args.log_dir, "prepare_data")

    try:
        # Validate paths
        validate_paths(
            training_excel=args.training_excel,
            testing_excel=args.testing_excel,
            prompt_template=args.prompt_template,
            output_dir=output_dir,
        )

        # Load prompt template
        prompt_sections = load_prompt_template(args.prompt_template, logger)

        # Load training data
        train_df = load_excel_data(args.training_excel, logger)
        train_examples = prepare_dataset(train_df, prompt_sections, logger)

        # Load testing data
        test_df = load_excel_data(args.testing_excel, logger)
        test_examples = prepare_dataset(test_df, prompt_sections, logger)

        # Save JSONL files
        save_jsonl(train_examples, train_jsonl)

        save_jsonl(test_examples, test_jsonl)

        # Generate and save statistics
        stats = generate_stats_report(train_examples, test_examples, logger)
        save_json(stats, data_stats_json)

        logger.info("Data preparation completed successfully.")
        logger.info(f"Outputs: {train_jsonl}, {test_jsonl}, {data_stats_json}")

        return 0

    except Exception as e:
        logger.error(f"Error during data preparation: {e}", exc_info=True)
        return 1

#%%
if __name__ == "__main__":
    sys.exit(main())
