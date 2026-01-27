"""
Data preparation for GPT fine-tuning on stance/agreement classification.

Supports: monetary_stance, fiscal_stance, monetary_agreement, fiscal_agreement
"""
#%%
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import Counter

import pandas as pd
from tqdm import tqdm

import training_config as config

PROJECT_ROOT = config.PROJECT_ROOT
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "libs"))
sys.path.insert(0, str(PROJECT_ROOT / "src/Traction/prompts"))

from libs.prompt_utils import load_prompt
from training_utils import (
    setup_logging, validate_dataframe, save_jsonl, save_json, format_prompt_with_vars,
)
from prompt_examples import (
    AUTHOR_TYPE_MAPPING, AUTHOR_TYPE_POSSESSIVE_MAPPING, AUTHOR_VERB_MAPPING,
    TASK_EXAMPLES, TASK_EXPLANATIONS,
)

#%%
def create_stance_example(
    row: pd.Series,
    text_col: str,
    author_type: str,
    label_cols: List[str],
    prompt_sections: Dict[str, str],
    task_type: str,
    task_config: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Create training example for stance tasks."""
    cols = task_config['excel_columns']
    text = row[text_col]

    if pd.isna(text) or not str(text).strip():
        return None

    labels = {}
    for col in label_cols:
        if pd.isna(row[col]):
            return None
        labels[col] = str(row[col]).strip()

    system_content = format_prompt_with_vars(prompt_sections['system'], {
        "TYPE": AUTHOR_TYPE_MAPPING.get(author_type, author_type),
        "TYPE_POSSESSIVE": AUTHOR_TYPE_POSSESSIVE_MAPPING.get(author_type, f"{author_type}'s"),
        "VERB": AUTHOR_VERB_MAPPING.get(author_type, 'stated'),
        "EXPLANATION": TASK_EXPLANATIONS.get(task_type, {}).get(author_type, ''),
        "EXAMPLES": TASK_EXAMPLES.get(task_type, {}).get(author_type, ''),
    })

    # Append schema to system prompt (matches format_messages behavior)
    if 'schema' in prompt_sections:
        system_content = f"{system_content}\n\n{prompt_sections['schema']}"

    user_content = format_prompt_with_vars(prompt_sections['user'], {
        "COUNTRY": str(row[cols['country']]),
        "YEAR": str(row[cols['year']]),
        "TEXT": str(text).strip(),
    })

    if task_type == 'fiscal_stance':
        response = {"stance_near_term": labels[label_cols[0]]}
    else:
        response = {"stance_current": labels[label_cols[0]], "stance_future": labels[label_cols[1]]}

    return {"messages": [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
        {"role": "assistant", "content": json.dumps(response)},
    ]}

#%%
def create_agreement_example(
    row: pd.Series,
    prompt_sections: Dict[str, str],
    task_config: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Create training example for agreement tasks."""
    cols = task_config['excel_columns']
    staff_text = row[cols['staff_text']]
    buff_text = row[cols['buff_text']]
    agreement = row[cols['agreement']]

    if pd.isna(staff_text) or pd.isna(buff_text) or pd.isna(agreement):
        return None
    if not str(staff_text).strip() or not str(buff_text).strip():
        return None

    disagreement = row.get(cols.get('disagreement_areas', ''), '')
    disagreement = "" if pd.isna(disagreement) else str(disagreement).strip()

    user_content = format_prompt_with_vars(prompt_sections['user'], {
        "COUNTRY": str(row[cols['country']]),
        "YEAR": str(row[cols['year']]),
        "STAFF_TEXT": str(staff_text).strip(),
        "AUTHORITY_TEXT": str(buff_text).strip(),
    })

    response = {"agreement": str(agreement).strip(), "disagreement_areas": disagreement}

    # Build system content with schema (matches format_messages behavior)
    system_content = prompt_sections['system']
    if 'schema' in prompt_sections:
        system_content = f"{system_content}\n\n{prompt_sections['schema']}"

    return {"messages": [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
        {"role": "assistant", "content": json.dumps(response)},
    ]}


def get_label_cols(task_type: str, author_type: str) -> List[str]:
    """Get label column names for a task/author combination."""
    cols = config.TASK_EXCEL_COLUMNS[task_type]
    if task_type == 'monetary_stance':
        return [cols[f'{author_type}_stance_current'], cols[f'{author_type}_stance_future']]
    elif task_type == 'fiscal_stance':
        return [cols[f'{author_type}_stance_near_term']]
    raise ValueError(f"Invalid task type for stance: {task_type}")


def prepare_dataset(
    df: pd.DataFrame,
    prompt_sections: Dict[str, str],
    task_type: str,
) -> List[Dict[str, Any]]:
    """Generate training examples from DataFrame."""
    examples = []
    task_config = config.get_task_config(task_type)
    cols = task_config['excel_columns']

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing"):
        if 'agreement' in task_type:
            ex = create_agreement_example(row, prompt_sections, task_config)
            if ex:
                examples.append(ex)
        else:
            for author in ['staff', 'buff']:
                ex = create_stance_example(
                    row, cols[f'{author}_text'], author,
                    get_label_cols(task_type, author),
                    prompt_sections, task_type, task_config,
                )
                if ex:
                    examples.append(ex)

    return examples


def extract_labels(examples: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Extract labels from examples for statistics."""
    results = {}
    for ex in examples:
        parsed = json.loads(ex['messages'][2]['content'])
        for key, val in parsed.items():
            if key not in results:
                results[key] = []
            results[key].append(val)
    return results


def generate_stats(
    train_examples: List[Dict[str, Any]],
    test_examples: List[Dict[str, Any]],
    task_type: str,
) -> Dict[str, Any]:
    """Calculate dataset statistics."""
    def text_stats(examples):
        lengths = [len(ex['messages'][1]['content']) for ex in examples]
        return {
            'mean': round(sum(lengths) / len(lengths), 2) if lengths else 0,
            'min': min(lengths) if lengths else 0,
            'max': max(lengths) if lengths else 0,
        }

    train_labels = extract_labels(train_examples)
    test_labels = extract_labels(test_examples)

    return {
        'task_type': task_type,
        'dataset_size': {
            'train': len(train_examples),
            'test': len(test_examples),
            'total': len(train_examples) + len(test_examples),
        },
        'label_distributions': {
            'train': {k: dict(Counter(v)) for k, v in train_labels.items()},
            'test': {k: dict(Counter(v)) for k, v in test_labels.items()},
        },
        'text_length': {
            'train': text_stats(train_examples),
            'test': text_stats(test_examples),
        },
    }

#%%
def resolve_paths(args: argparse.Namespace) -> Dict[str, Path]:
    """Resolve paths using CLI args or task-specific defaults."""
    cfg = config.get_task_config(args.task_type)
    output_dir = args.output_dir or cfg['output_dir']
    return {
        'training_excel': args.training_excel or cfg['training_excel'],
        'testing_excel': args.testing_excel or cfg['testing_excel'],
        'prompt_template': args.prompt_template or cfg['prompt_template'],
        'output_dir': output_dir,
        'train_jsonl': output_dir / f"train_{args.task_type}.jsonl",
        'test_jsonl': output_dir / f"test_{args.task_type}.jsonl",
        'stats_json': output_dir / f"data_stats_{args.task_type}.json",
    }

def validate_paths(paths: Dict[str, Path]):
    missing = [str(p) for k, p in paths.items()
               if k in ('training_excel', 'testing_excel', 'prompt_template') and not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing files:\n" + "\n".join(f"  - {p}" for p in missing))
    paths['output_dir'].mkdir(parents=True, exist_ok=True)

def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare JSONL for fine-tuning.")
    parser.add_argument("--task-type", type=str, choices=config.TASK_TYPES,
                        default=config.DEFAULT_TASK_TYPE)
    parser.add_argument("--training-excel", type=Path, default=None)
    parser.add_argument("--testing-excel", type=Path, default=None)
    parser.add_argument("--prompt-template", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--log-dir", type=Path, default=config.LOG_DIR)
    parser.add_argument("--test-mode", action="store_true", help="Process only first 10 rows")
    return parser.parse_args(args)

#%%
def main():
    args = parse_args()
    logger = setup_logging(args.log_dir, "prepare_data")
    paths = resolve_paths(args)

    try:
        validate_paths(paths)
        prompt_sections = load_prompt(paths['prompt_template']).sections

        train_df = pd.read_excel(paths['training_excel'])
        test_df = pd.read_excel(paths['testing_excel'])
        validate_dataframe(train_df, config.get_required_columns(args.task_type))
        validate_dataframe(test_df, config.get_required_columns(args.task_type))

        if args.test_mode:
            train_df, test_df = train_df.head(10), test_df.head(10)

        train_examples = prepare_dataset(train_df, prompt_sections, args.task_type)
        test_examples = prepare_dataset(test_df, prompt_sections, args.task_type)

        save_jsonl(train_examples, paths['train_jsonl'])
        save_jsonl(test_examples, paths['test_jsonl'])
        save_json(generate_stats(train_examples, test_examples, args.task_type), paths['stats_json'])

        logger.info(f"Task: {args.task_type} | Train: {len(train_examples)} | Test: {len(test_examples)}")
        logger.info(f"Output: {paths['train_jsonl']}")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    return 0


if __name__ == "__main__":
    main()


# %%
