"""
Evaluate fine-tuned GPT model on stance/agreement classification.

Supports: monetary_stance, fiscal_stance, monetary_agreement, fiscal_agreement

Outputs:
- Evaluation report (markdown)
- Predictions Excel file with input data, ground truth, and predictions
"""
#%%
import os
import re
import sys
import json
import argparse
import asyncio
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import training_config as config
from training_utils import setup_logging, load_jsonl, write_evaluation_report
# Setup imports
PROJECT_ROOT = config.PROJECT_ROOT
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'libs'))
sys.path.insert(0, str(PROJECT_ROOT / 'src/Traction'))
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')
from llm_factory_openai import BatchAsyncLLMAgent
from llm_batch_process_utils import _process_batch_async
#%%
def parse_args(args=None):
    parser = argparse.ArgumentParser(description="Evaluate fine-tuned model")
    parser.add_argument('--task-type', choices=config.TASK_TYPES, default=config.DEFAULT_TASK_TYPE)
    parser.add_argument('--model-id', required=True, help='Fine-tuned model ID')
    parser.add_argument('--test-file', type=Path, default=None)
    parser.add_argument('--batch-size', type=int, default=8)
    return parser.parse_args(args)

def load_test_data(test_file: Path) -> Tuple[List, List[Dict], List[str]]:
    """Load test JSONL and return (messages, labels, user_contents)."""
    data = load_jsonl(test_file)
    messages = [item['messages'][:2] for item in data]  # system + user
    labels = [json.loads(item['messages'][2]['content']) for item in data]  # assistant
    user_contents = [item['messages'][1]['content'] for item in data]  # user message text
    return messages, labels, user_contents


def extract_metadata_from_user_content(user_content: str, task_type: str) -> Dict[str, str]:
    """
    Extract metadata (country, year, text) from user message content.

    The user content follows patterns like:
    - Stance: "Country: {country}\nYear: {year}\n\nText:\n{text}"
    - Agreement: "Country: {country}\nYear: {year}\n\nIMF Staff Assessment:\n{staff}\n\nAuthority Statement:\n{auth}"
    """
    metadata = {}

    # Extract country
    country_match = re.search(r'Country:\s*(.+?)(?:\n|$)', user_content)
    if country_match:
        metadata['country'] = country_match.group(1).strip()

    # Extract year
    year_match = re.search(r'Year:\s*(\d+)', user_content)
    if year_match:
        metadata['year'] = year_match.group(1).strip()

    if 'agreement' in task_type:
        # Agreement task - extract both staff and authority text
        staff_match = re.search(r'IMF Staff Assessment:\s*\n(.+?)(?:\n\nAuthority|\n\nCountry Authority)', user_content, re.DOTALL)
        if staff_match:
            metadata['staff_text'] = staff_match.group(1).strip()[:500] + "..." if len(staff_match.group(1).strip()) > 500 else staff_match.group(1).strip()

        auth_match = re.search(r'(?:Authority Statement|Country Authority Statement):\s*\n(.+?)$', user_content, re.DOTALL)
        if auth_match:
            metadata['authority_text'] = auth_match.group(1).strip()[:500] + "..." if len(auth_match.group(1).strip()) > 500 else auth_match.group(1).strip()
    else:
        # Stance task - extract single text
        text_match = re.search(r'Text:\s*\n(.+?)$', user_content, re.DOTALL)
        if text_match:
            text = text_match.group(1).strip()
            metadata['text'] = text[:500] + "..." if len(text) > 500 else text

        # Try to determine author type from system prompt context (will be added separately)

    return metadata

def compute_metrics(predictions: List[str], labels: List[str], combine_unclear: bool = False):
    """Compute accuracy, precision, recall, F1 for a single field."""
    valid = [(p, l) for p, l in zip(predictions, labels) if p is not None and l is not None]
    if not valid:
        return {'accuracy': 0, 'precision': 0, 'recall': 0, 'f1': 0}

    preds, gts = zip(*valid)

    if combine_unclear:
        preds = ['unclear' if p in ('unclear', 'irrelevant') else p for p in preds]
        gts = ['unclear' if g in ('unclear', 'irrelevant') else g for g in gts]

    return {
        'accuracy': accuracy_score(gts, preds),
        'precision': precision_score(gts, preds, average='weighted', zero_division=0),
        'recall': recall_score(gts, preds, average='weighted', zero_division=0),
        'f1': f1_score(gts, preds, average='weighted', zero_division=0),
    }


def run_inference(model_id: str, messages: List, batch_size: int) -> List[Dict]:
    """Run batch inference and return list of parsed response dicts."""
    agent = BatchAsyncLLMAgent(
        api_key=os.getenv('OPENAI_API_KEY'),
        model=model_id,
        temperature=config.TEMPERATURE,
    )

    async def batch_infer():
        return await _process_batch_async(agent, messages, response_model=None, batch_size=batch_size, max_completion_tokens=2000, seed=config.SEED)

    results = asyncio.run(batch_infer())

    parsed = []
    for r in results:
        if r is None:
            parsed.append(None)
        else:
            try:
                parsed.append(agent.parse_json(r))
            except json.JSONDecodeError:
                parsed.append(None)
    return parsed


def evaluate(predictions: List[Dict], labels: List[Dict], task_type: str) -> Dict:
    """Evaluate predictions against labels for all fields in task."""
    output_fields = config.TASK_OUTPUT_FIELDS[task_type]
    eval_fields = [f for f in output_fields if f != 'disagreement_areas']
    is_stance_task = 'stance' in task_type

    results = {}
    for field in eval_fields:
        preds = [p.get(field) if p else None for p in predictions]
        gts = [l.get(field) for l in labels]

        results[field] = compute_metrics(preds, gts)
        if is_stance_task:
            results[f'{field}_combined'] = compute_metrics(preds, gts, combine_unclear=True)

    return results


def create_predictions_dataframe(
    predictions: List[Dict],
    labels: List[Dict],
    user_contents: List[str],
    messages: List,
    task_type: str,
) -> pd.DataFrame:
    """
    Create a DataFrame with predictions, ground truth, and input data.

    Returns DataFrame with columns:
    - country, year
    - input text(s)
    - ground truth labels
    - predicted labels
    - correct flags for each field
    """
    output_fields = config.TASK_OUTPUT_FIELDS[task_type]
    eval_fields = [f for f in output_fields if f != 'disagreement_areas']

    rows = []
    for i, (pred, label, user_content, msg) in enumerate(zip(predictions, labels, user_contents, messages)):
        # Extract metadata from user content
        metadata = extract_metadata_from_user_content(user_content, task_type)

        # Try to extract author type from system message for stance tasks
        if 'stance' in task_type:
            system_content = msg[0]['content'] if msg else ''
            if 'IMF staff' in system_content:
                metadata['author'] = 'IMF staff'
            elif 'country authority' in system_content.lower():
                metadata['author'] = 'country authority'

        row = {
            'index': i,
            'country': metadata.get('country', ''),
            'year': metadata.get('year', ''),
        }

        # Add text columns based on task type
        if 'agreement' in task_type:
            row['staff_text'] = metadata.get('staff_text', '')
            row['authority_text'] = metadata.get('authority_text', '')
        else:
            row['author'] = metadata.get('author', '')
            row['text'] = metadata.get('text', '')

        # Add ground truth and predictions for each field
        for field in eval_fields:
            gt_val = label.get(field) if label else None
            pred_val = pred.get(field) if pred else None

            row[f'gt_{field}'] = gt_val
            row[f'pred_{field}'] = pred_val
            row[f'correct_{field}'] = (gt_val == pred_val) if (gt_val is not None and pred_val is not None) else None

        # For agreement tasks, also include disagreement_areas if present
        if 'agreement' in task_type:
            row['gt_disagreement_areas'] = label.get('disagreement_areas', '') if label else ''
            row['pred_disagreement_areas'] = pred.get('disagreement_areas', '') if pred else ''

        rows.append(row)

    return pd.DataFrame(rows)


def export_predictions_excel(df: pd.DataFrame, output_path: Path, task_type: str):
    """Export predictions DataFrame to Excel with formatting."""
    # Reorder columns for better readability
    base_cols = ['index', 'country', 'year']

    if 'agreement' in task_type:
        text_cols = ['staff_text', 'authority_text']
    else:
        text_cols = ['author', 'text']

    # Get evaluation field columns
    output_fields = config.TASK_OUTPUT_FIELDS[task_type]
    eval_fields = [f for f in output_fields if f != 'disagreement_areas']

    eval_cols = []
    for field in eval_fields:
        eval_cols.extend([f'gt_{field}', f'pred_{field}', f'correct_{field}'])

    # Add disagreement_areas for agreement tasks
    if 'agreement' in task_type:
        eval_cols.extend(['gt_disagreement_areas', 'pred_disagreement_areas'])

    # Reorder columns
    all_cols = base_cols + text_cols + eval_cols
    existing_cols = [c for c in all_cols if c in df.columns]
    df = df[existing_cols]

    # Export to Excel
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Predictions')

        # Add a summary sheet with error analysis
        error_df = df[df[[c for c in df.columns if c.startswith('correct_')]].eq(False).any(axis=1)]
        if not error_df.empty:
            error_df.to_excel(writer, index=False, sheet_name='Errors Only')

    return output_path

#%%
def main():
    args = parse_args()
    logger = setup_logging(config.LOG_DIR, "evaluate")

    # Get paths
    task_config = config.get_task_config(args.task_type)
    output_dir = task_config['output_dir']
    test_file = args.test_file or (output_dir / f"test_{args.task_type}.jsonl")

    if not test_file.exists():
        print(f"Error: Test file not found: {test_file}")
        print(f"Run: python prepare_data.py --task-type {args.task_type}")
        sys.exit(1)

    logger.info(f"Task: {args.task_type}, Model: {args.model_id}")
    print(f"\nEvaluating {args.task_type} with model {args.model_id}")

    # Load data and run inference
    messages, labels, user_contents = load_test_data(test_file)
    print(f"Loaded {len(messages)} test samples")

    predictions = run_inference(args.model_id, messages, args.batch_size)
    success_rate = sum(1 for p in predictions if p) / len(predictions)
    print(f"Inference complete: {success_rate:.1%} success rate")

    # Evaluate
    results = evaluate(predictions, labels, args.task_type)

    # Print results
    print("\nResults:")
    for field, metrics in results.items():
        print(f"  {field}: acc={metrics['accuracy']:.4f}, f1={metrics['f1']:.4f}")

    # Save report
    report_file = output_dir / f"evaluation_report_{args.task_type}.md"
    write_evaluation_report(results, args.model_id, args.task_type, report_file)

    # Create and export predictions DataFrame
    print("\nExporting predictions to Excel...")
    predictions_df = create_predictions_dataframe(
        predictions, labels, user_contents, messages, args.task_type
    )
    excel_file = output_dir / f"predictions_{args.task_type}.xlsx"
    export_predictions_excel(predictions_df, excel_file, args.task_type)
    print(f"Predictions saved to: {excel_file}")

    # Print error summary
    eval_fields = [f for f in config.TASK_OUTPUT_FIELDS[args.task_type] if f != 'disagreement_areas']
    for field in eval_fields:
        correct_col = f'correct_{field}'
        if correct_col in predictions_df.columns:
            n_correct = predictions_df[correct_col].sum()
            n_total = predictions_df[correct_col].notna().sum()
            n_errors = n_total - n_correct
            print(f"  {field}: {n_errors} errors out of {n_total} samples")

    logger.info("Evaluation complete")


if __name__ == "__main__":
    main()
