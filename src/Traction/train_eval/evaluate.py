"""
Evaluation script for fine-tuned GPT-5-mini model.

Runs inference on test set and calculates comprehensive metrics for
monetary stance classification.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pandas as pd
from tqdm import tqdm
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report,
)

# Add project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import training_config as config
from training_utils import (
    setup_logging,
    load_openai_client,
    load_jsonl,
    save_json,
    load_json,
    handle_api_error,
)


# ============================================================================
# Inference
# ============================================================================

@handle_api_error(max_retries=config.MAX_RETRIES, backoff=config.RETRY_BACKOFF)
def run_single_inference(messages: List[Dict[str, str]], model_id: str, client) -> str:
    """
    Run single inference call with retry logic.

    Args:
        messages: List of message dicts (system, user)
        model_id: Fine-tuned model ID
        client: OpenAI client

    Returns:
        Assistant response content
    """
    response = client.chat.completions.create(
        model=model_id,
        messages=messages,
        temperature=config.TEMPERATURE,
    )

    return response.choices[0].message.content


def run_inference(
    test_examples: List[Dict[str, Any]],
    model_id: str,
    client,
    logger,
) -> List[Dict[str, Any]]:
    """
    Run inference on test set with progress tracking.

    Args:
        test_examples: Test examples in OpenAI format
        model_id: Fine-tuned model ID
        client: OpenAI client
        logger: Logger instance

    Returns:
        List of results with predictions
    """
    logger.info(f"Running inference on {len(test_examples)} test examples...")
    logger.info(f"Model: {model_id}")
    logger.info(f"Temperature: {config.TEMPERATURE}")

    results = []

    for example in tqdm(test_examples, desc="Inference"):
        # Extract messages (exclude assistant message for inference)
        messages = example['messages'][:2]  # System + User only

        # Get ground truth
        ground_truth = json.loads(example['messages'][2]['content'])

        # Run inference
        try:
            prediction_str = run_single_inference(messages, model_id, client)
            error = None
        except Exception as e:
            logger.warning(f"Inference failed: {e}")
            prediction_str = None
            error = str(e)

        # Store result
        results.append({
            'messages': example['messages'],
            'ground_truth': ground_truth,
            'prediction_str': prediction_str,
            'error': error,
        })

    logger.info(f"✓ Completed {len(results)} inferences")

    # Count errors
    error_count = sum(1 for r in results if r['error'])
    if error_count > 0:
        logger.warning(f"  {error_count} inference errors")

    return results


# ============================================================================
# Parsing
# ============================================================================

def parse_predictions(
    results: List[Dict[str, Any]],
    logger,
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """
    Parse assistant JSON responses and extract labels.

    Args:
        results: Inference results
        logger: Logger instance

    Returns:
        Tuple of (true_current, pred_current, true_future, pred_future)
    """
    logger.info("Parsing predictions...")

    true_current = []
    pred_current = []
    true_future = []
    pred_future = []

    parse_errors = 0

    for result in results:
        # Ground truth
        gt = result['ground_truth']
        true_current.append(gt['stance_current'])
        true_future.append(gt['stance_future'])

        # Prediction
        if result['error']:
            # Inference error
            pred_current.append('error')
            pred_future.append('error')
            parse_errors += 1
        else:
            try:
                # Parse JSON
                pred = json.loads(result['prediction_str'])

                # Extract labels
                pred_current.append(pred.get('stance_current', 'error'))
                pred_future.append(pred.get('stance_future', 'error'))

                # Validate labels
                if pred.get('stance_current') not in config.STANCE_CURRENT_LABELS:
                    logger.warning(f"Invalid current stance: {pred.get('stance_current')}")
                    pred_current[-1] = 'error'
                    parse_errors += 1

                if pred.get('stance_future') not in config.STANCE_FUTURE_LABELS:
                    logger.warning(f"Invalid future stance: {pred.get('stance_future')}")
                    pred_future[-1] = 'error'
                    parse_errors += 1

            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error: {e}")
                logger.warning(f"  Response: {result['prediction_str'][:100]}")
                pred_current.append('error')
                pred_future.append('error')
                parse_errors += 1

    logger.info(f"✓ Parsed {len(results)} predictions")
    if parse_errors > 0:
        logger.warning(f"  {parse_errors} parse errors")

    return true_current, pred_current, true_future, pred_future


# ============================================================================
# Metrics
# ============================================================================

def calculate_metrics(
    y_true: List[str],
    y_pred: List[str],
    label_name: str,
    logger,
) -> Dict[str, Any]:
    """
    Calculate classification metrics for single task.

    Args:
        y_true: Ground truth labels
        y_pred: Predicted labels
        label_name: Task name (for logging)
        logger: Logger instance

    Returns:
        Dictionary with metrics
    """
    logger.info(f"Calculating metrics for: {label_name}")

    # Filter out errors
    valid_indices = [i for i, pred in enumerate(y_pred) if pred != 'error']
    y_true_valid = [y_true[i] for i in valid_indices]
    y_pred_valid = [y_pred[i] for i in valid_indices]

    if not y_true_valid:
        logger.error(f"No valid predictions for {label_name}")
        return {}

    # Get unique labels
    labels = sorted(set(y_true_valid + y_pred_valid))

    # Calculate metrics
    accuracy = accuracy_score(y_true_valid, y_pred_valid)
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true_valid,
        y_pred_valid,
        labels=labels,
        average=None,
        zero_division=0
    )

    # Macro and weighted averages
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true_valid, y_pred_valid, average='macro', zero_division=0
    )
    precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(
        y_true_valid, y_pred_valid, average='weighted', zero_division=0
    )

    # Confusion matrix
    cm = confusion_matrix(y_true_valid, y_pred_valid, labels=labels)

    # Classification report
    report = classification_report(
        y_true_valid,
        y_pred_valid,
        labels=labels,
        zero_division=0
    )

    # Per-label metrics
    label_metrics = {}
    for i, label in enumerate(labels):
        label_metrics[label] = {
            'precision': float(precision[i]),
            'recall': float(recall[i]),
            'f1': float(f1[i]),
            'support': int(support[i])
        }

    metrics = {
        'accuracy': float(accuracy),
        'precision_macro': float(precision_macro),
        'recall_macro': float(recall_macro),
        'f1_macro': float(f1_macro),
        'precision_weighted': float(precision_weighted),
        'recall_weighted': float(recall_weighted),
        'f1_weighted': float(f1_weighted),
        'confusion_matrix': cm.tolist(),
        'labels': labels,
        'label_metrics': label_metrics,
        'classification_report': report,
        'n_samples': len(y_true_valid),
        'n_errors': len(y_true) - len(y_true_valid),
    }

    # Log summary
    logger.info(f"  Accuracy: {accuracy:.4f}")
    logger.info(f"  F1 (macro): {f1_macro:.4f}")
    logger.info(f"  F1 (weighted): {f1_weighted:.4f}")
    logger.info(f"  Samples: {len(y_true_valid)} (errors: {len(y_true) - len(y_true_valid)})")

    return metrics


# ============================================================================
# Report Generation
# ============================================================================

def generate_evaluation_report(
    metrics_current: Dict[str, Any],
    metrics_future: Dict[str, Any],
    test_examples: List[Dict[str, Any]],
    model_id: str,
    logger,
) -> str:
    """
    Generate markdown evaluation report.

    Args:
        metrics_current: Metrics for current stance
        metrics_future: Metrics for future stance
        test_examples: Test examples
        model_id: Model ID
        logger: Logger instance

    Returns:
        Markdown report string
    """
    logger.info("Generating evaluation report...")

    report = []

    # Header
    report.append("# Fine-Tuned Model Evaluation Report")
    report.append("")
    report.append(f"**Model ID**: `{model_id}`")
    report.append(f"**Base Model**: `{config.BASE_MODEL}`")
    report.append(f"**Evaluation Date**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # Dataset info
    report.append("## Dataset Statistics")
    report.append("")
    report.append(f"- **Test samples**: {len(test_examples)}")
    report.append(f"- **Current stance samples**: {metrics_current.get('n_samples', 0)}")
    report.append(f"- **Future stance samples**: {metrics_future.get('n_samples', 0)}")
    report.append(f"- **Parse errors (current)**: {metrics_current.get('n_errors', 0)}")
    report.append(f"- **Parse errors (future)**: {metrics_future.get('n_errors', 0)}")
    report.append("")

    # Overall performance
    overall_accuracy = (
        metrics_current.get('accuracy', 0) + metrics_future.get('accuracy', 0)
    ) / 2

    report.append("## Overall Performance")
    report.append("")
    report.append(f"- **Average Accuracy**: {overall_accuracy:.4f}")
    report.append("")

    # Current stance metrics
    report.append("## Current Stance Classification")
    report.append("")
    report.append(f"- **Accuracy**: {metrics_current.get('accuracy', 0):.4f}")
    report.append(f"- **F1 Score (Macro)**: {metrics_current.get('f1_macro', 0):.4f}")
    report.append(f"- **F1 Score (Weighted)**: {metrics_current.get('f1_weighted', 0):.4f}")
    report.append("")

    # Per-label metrics for current
    report.append("### Per-Label Performance (Current Stance)")
    report.append("")
    report.append("| Label | Precision | Recall | F1 Score | Support |")
    report.append("|-------|-----------|--------|----------|---------|")
    for label, m in metrics_current.get('label_metrics', {}).items():
        report.append(
            f"| {label} | {m['precision']:.4f} | {m['recall']:.4f} | "
            f"{m['f1']:.4f} | {m['support']} |"
        )
    report.append("")

    # Confusion matrix for current
    report.append("### Confusion Matrix (Current Stance)")
    report.append("")
    report.append("```")
    labels_current = metrics_current.get('labels', [])
    cm_current = metrics_current.get('confusion_matrix', [])
    if labels_current and cm_current:
        # Header
        header = "True \\ Pred | " + " | ".join(labels_current)
        report.append(header)
        report.append("-" * len(header))
        # Rows
        for i, label in enumerate(labels_current):
            row = f"{label:12} | " + " | ".join(str(cm_current[i][j]) for j in range(len(labels_current)))
            report.append(row)
    report.append("```")
    report.append("")

    # Future stance metrics
    report.append("## Future Stance Classification")
    report.append("")
    report.append(f"- **Accuracy**: {metrics_future.get('accuracy', 0):.4f}")
    report.append(f"- **F1 Score (Macro)**: {metrics_future.get('f1_macro', 0):.4f}")
    report.append(f"- **F1 Score (Weighted)**: {metrics_future.get('f1_weighted', 0):.4f}")
    report.append("")

    # Per-label metrics for future
    report.append("### Per-Label Performance (Future Stance)")
    report.append("")
    report.append("| Label | Precision | Recall | F1 Score | Support |")
    report.append("|-------|-----------|--------|----------|---------|")
    for label, m in metrics_future.get('label_metrics', {}).items():
        report.append(
            f"| {label} | {m['precision']:.4f} | {m['recall']:.4f} | "
            f"{m['f1']:.4f} | {m['support']} |"
        )
    report.append("")

    # Confusion matrix for future
    report.append("### Confusion Matrix (Future Stance)")
    report.append("")
    report.append("```")
    labels_future = metrics_future.get('labels', [])
    cm_future = metrics_future.get('confusion_matrix', [])
    if labels_future and cm_future:
        # Header
        header = "True \\ Pred | " + " | ".join(labels_future)
        report.append(header)
        report.append("-" * len(header))
        # Rows
        for i, label in enumerate(labels_future):
            row = f"{label:16} | " + " | ".join(str(cm_future[i][j]) for j in range(len(labels_future)))
            report.append(row)
    report.append("```")
    report.append("")

    # Classification reports
    report.append("## Detailed Classification Reports")
    report.append("")
    report.append("### Current Stance")
    report.append("```")
    report.append(metrics_current.get('classification_report', ''))
    report.append("```")
    report.append("")
    report.append("### Future Stance")
    report.append("```")
    report.append(metrics_future.get('classification_report', ''))
    report.append("```")
    report.append("")

    markdown = "\n".join(report)
    logger.info("✓ Report generated")

    return markdown


# ============================================================================
# Argument Parsing
# ============================================================================

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for evaluation script.

    Returns:
        Parsed arguments namespace with the following attributes:
        - model_id: Fine-tuned model ID (optional, loads from metadata if not provided)
        - test_file: Path to test JSONL file
    """
    parser = argparse.ArgumentParser(
        description="Evaluate fine-tuned GPT-5-mini model"
    )
    parser.add_argument(
        '--model-id',
        type=str,
        required=False,
        help='Fine-tuned model ID (if not specified, loads from metadata)'
    )
    parser.add_argument(
        '--test-file',
        type=Path,
        default=config.TEST_JSONL,
        help='Path to test JSONL file'
    )

    return parser.parse_args()


# ============================================================================
# Main Pipeline
# ============================================================================

def main():
    """Main execution pipeline."""
    # Parse command-line arguments
    args = parse_arguments()

    # Setup logging
    logger = setup_logging(config.LOG_DIR, "evaluate")

    logger.info("="*60)
    logger.info("Starting evaluation pipeline")
    logger.info("="*60)

    try:
        # Check test file exists
        if not args.test_file.exists():
            raise FileNotFoundError(
                f"Test file not found: {args.test_file}\n"
                f"Please run prepare_data.py first."
            )

        # Get model ID
        if args.model_id:
            model_id = args.model_id
        else:
            # Load from metadata
            if not config.FINETUNING_METADATA_JSON.exists():
                raise FileNotFoundError(
                    f"Metadata not found: {config.FINETUNING_METADATA_JSON}\n"
                    f"Please specify --model-id or run finetune.py first."
                )
            metadata = load_json(config.FINETUNING_METADATA_JSON)
            model_id = metadata.get('fine_tuned_model_id')
            if not model_id:
                raise ValueError("Model ID not found in metadata")
            logger.info(f"Loaded model ID from metadata: {model_id}")

        # Load OpenAI client
        client = load_openai_client()

        # Load test data
        test_examples = load_jsonl(args.test_file)
        logger.info(f"Loaded {len(test_examples)} test examples")

        # Run inference
        results = run_inference(test_examples, model_id, client, logger)

        # Parse predictions
        true_current, pred_current, true_future, pred_future = parse_predictions(
            results, logger
        )

        # Calculate metrics
        metrics_current = calculate_metrics(
            true_current, pred_current, "stance_current", logger
        )
        metrics_future = calculate_metrics(
            true_future, pred_future, "stance_future", logger
        )

        # Generate report
        report = generate_evaluation_report(
            metrics_current, metrics_future, test_examples, model_id, logger
        )

        # Save report
        logger.info(f"Saving evaluation report to: {config.EVALUATION_REPORT_MD}")
        with open(config.EVALUATION_REPORT_MD, 'w') as f:
            f.write(report)

        # Save raw metrics
        all_metrics = {
            'model_id': model_id,
            'test_samples': len(test_examples),
            'stance_current': metrics_current,
            'stance_future': metrics_future,
            'overall_accuracy': (
                metrics_current.get('accuracy', 0) + metrics_future.get('accuracy', 0)
            ) / 2,
        }
        logger.info(f"Saving metrics to: {config.METRICS_JSON}")
        save_json(all_metrics, config.METRICS_JSON)

        # Save predictions to CSV
        logger.info(f"Saving predictions to: {config.PREDICTIONS_CSV}")
        predictions_df = pd.DataFrame({
            'true_current': true_current,
            'pred_current': pred_current,
            'true_future': true_future,
            'pred_future': pred_future,
        })
        predictions_df.to_csv(config.PREDICTIONS_CSV, index=False)

        logger.info("="*60)
        logger.info("✓ Evaluation completed successfully!")
        logger.info("="*60)
        logger.info(f"Overall accuracy: {all_metrics['overall_accuracy']:.4f}")
        logger.info(f"Current stance accuracy: {metrics_current.get('accuracy', 0):.4f}")
        logger.info(f"Future stance accuracy: {metrics_future.get('accuracy', 0):.4f}")
        logger.info("\nOutput files:")
        logger.info(f"  - {config.EVALUATION_REPORT_MD}")
        logger.info(f"  - {config.METRICS_JSON}")
        logger.info(f"  - {config.PREDICTIONS_CSV}")

        return 0

    except Exception as e:
        logger.error(f"Error during evaluation: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
