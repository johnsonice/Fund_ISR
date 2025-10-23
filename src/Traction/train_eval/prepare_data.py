"""
Data preparation script for GPT-5-mini fine-tuning.

Converts Excel data to OpenAI JSONL format for monetary stance classification.
Creates dual examples (staff + authority) from each row.
"""
#%%
import sys
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

    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # Validate required columns
    required_cols = list(config.EXCEL_COLUMNS.values())
    validate_dataframe(df, required_cols)

    logger.info(f"✓ All required columns present")

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

    # Extract sections
    sections = prompt.sections

    logger.info(f"✓ Loaded prompt with sections: {list(sections.keys())}")

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

    logger.info("Generating training examples...")

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

    logger.info(f"✓ Generated {len(examples)} examples from {len(df)} rows")

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
    logger.info("Generating statistics report...")

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

    # Log summary
    logger.info(f"\n{'='*60}")
    logger.info("Dataset Statistics:")
    logger.info(f"{'='*60}")
    logger.info(f"Training examples: {stats['dataset_size']['train']}")
    logger.info(f"Test examples: {stats['dataset_size']['test']}")
    logger.info(f"Total examples: {stats['dataset_size']['total']}")
    logger.info(f"\nTrain - Current stance distribution:")
    for label, count in stats['label_distributions']['train']['stance_current'].items():
        logger.info(f"  {label}: {count}")
    logger.info(f"\nTrain - Future stance distribution:")
    for label, count in stats['label_distributions']['train']['stance_future'].items():
        logger.info(f"  {label}: {count}")
    logger.info(f"{'='*60}\n")

    return stats

#%%
# ============================================================================
# Main Pipeline
# ============================================================================

def main():
    """Main execution pipeline."""
    # Setup logging
    logger = setup_logging(config.LOG_DIR, "prepare_data")

    logger.info("="*60)
    logger.info("Starting data preparation pipeline")
    logger.info("="*60)

    try:
        # Validate paths
        config.validate_paths()

        # Load prompt template
        prompt_sections = load_prompt_template(config.PROMPT_TEMPLATE_PATH, logger)

        # Load training data
        train_df = load_excel_data(config.TRAINING_EXCEL, logger)
        train_examples = prepare_dataset(train_df, prompt_sections, logger)

        # Load testing data
        test_df = load_excel_data(config.TESTING_EXCEL, logger)
        test_examples = prepare_dataset(test_df, prompt_sections, logger)

        # Save JSONL files
        logger.info(f"Saving training data to: {config.TRAIN_JSONL}")
        save_jsonl(train_examples, config.TRAIN_JSONL)

        logger.info(f"Saving test data to: {config.TEST_JSONL}")
        save_jsonl(test_examples, config.TEST_JSONL)

        # Generate and save statistics
        stats = generate_stats_report(train_examples, test_examples, logger)
        logger.info(f"Saving statistics to: {config.DATA_STATS_JSON}")
        save_json(stats, config.DATA_STATS_JSON)

        logger.info("="*60)
        logger.info("✓ Data preparation completed successfully!")
        logger.info("="*60)
        logger.info(f"Output files:")
        logger.info(f"  - {config.TRAIN_JSONL}")
        logger.info(f"  - {config.TEST_JSONL}")
        logger.info(f"  - {config.DATA_STATS_JSON}")

        return 0

    except Exception as e:
        logger.error(f"Error during data preparation: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
