"""
End-to-end fine-tuning pipeline orchestrator.

Runs complete workflow: prepare_data → finetune → evaluate
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

import training_config as config

# Add project paths using config
PROJECT_ROOT = config.PROJECT_ROOT
sys.path.insert(0, str(PROJECT_ROOT))
from training_utils import setup_logging, load_json

# Import pipeline modules
import prepare_data
import finetune
import evaluate


# ============================================================================
# Pipeline Orchestration
# ============================================================================

def check_file_exists(file_path: Path, description: str, logger) -> bool:
    """
    Check if file exists and log result.

    Args:
        file_path: Path to check
        description: File description for logging
        logger: Logger instance

    Returns:
        True if exists, False otherwise
    """
    exists = file_path.exists()
    status = "✓" if exists else "✗"
    logger.info(f"  {status} {description}: {file_path}")
    return exists


def run_complete_pipeline(args, logger):
    """
    Run complete pipeline with checkpoint support.

    Args:
        args: Command-line arguments
        logger: Logger instance

    Returns:
        Exit code (0 for success)
    """
    pipeline_start = datetime.now()
    logger.info("="*60)
    logger.info("Fine-Tuning Pipeline - Full Execution")
    logger.info("="*60)

    # Track completion
    steps_completed = []

    # ========================================================================
    # Step 1: Prepare Data
    # ========================================================================

    if args.skip_prepare:
        logger.info("\nStep 1: Data Preparation - SKIPPED")
        logger.info("Checking for existing data files...")

        train_exists = check_file_exists(config.TRAIN_JSONL, "Training data", logger)
        test_exists = check_file_exists(config.TEST_JSONL, "Test data", logger)

        if not (train_exists and test_exists):
            logger.error("Required data files not found. Cannot skip preparation.")
            return 1

        logger.info("✓ Using existing data files")

    else:
        logger.info("\nStep 1: Data Preparation")
        logger.info("-" * 60)

        try:
            # Run prepare_data module
            exit_code = prepare_data.main()

            if exit_code != 0:
                logger.error("Data preparation failed")
                return exit_code

            steps_completed.append("prepare_data")
            logger.info("✓ Data preparation completed")

        except Exception as e:
            logger.error(f"Error during data preparation: {e}", exc_info=True)
            return 1

    # ========================================================================
    # Step 2: Fine-Tune Model
    # ========================================================================

    if args.skip_finetune:
        logger.info("\nStep 2: Fine-Tuning - SKIPPED")
        logger.info("Checking for existing fine-tuning metadata...")

        metadata_exists = check_file_exists(
            config.FINETUNING_METADATA_JSON,
            "Fine-tuning metadata",
            logger
        )

        if not metadata_exists:
            logger.error("Metadata not found. Cannot skip fine-tuning.")
            return 1

        # Load model ID from metadata
        metadata = load_json(config.FINETUNING_METADATA_JSON)
        model_id = metadata.get('fine_tuned_model_id')

        if not model_id:
            logger.error("Model ID not found in metadata")
            return 1

        logger.info(f"✓ Using existing model: {model_id}")

    elif args.dry_run:
        logger.info("\nStep 2: Fine-Tuning - SKIPPED (dry run)")
        logger.info("Dry run mode: stopping before fine-tuning")
        logger.info("To run fine-tuning, remove --dry-run flag")
        return 0

    else:
        logger.info("\nStep 2: Fine-Tuning")
        logger.info("-" * 60)

        try:
            # Override sys.argv for finetune module
            original_argv = sys.argv
            sys.argv = ['finetune.py']

            if args.n_epochs:
                sys.argv.extend(['--n-epochs', str(args.n_epochs)])
            if args.learning_rate_multiplier:
                sys.argv.extend(['--learning-rate-multiplier', str(args.learning_rate_multiplier)])
            if args.suffix:
                sys.argv.extend(['--suffix', args.suffix])

            # Run finetune module
            exit_code = finetune.main()

            # Restore sys.argv
            sys.argv = original_argv

            if exit_code != 0:
                logger.error("Fine-tuning failed")
                return exit_code

            steps_completed.append("finetune")
            logger.info("✓ Fine-tuning completed")

            # Load model ID
            metadata = load_json(config.FINETUNING_METADATA_JSON)
            model_id = metadata.get('fine_tuned_model_id')

        except Exception as e:
            logger.error(f"Error during fine-tuning: {e}", exc_info=True)
            return 1

    # ========================================================================
    # Step 3: Evaluate Model
    # ========================================================================

    if args.skip_evaluate:
        logger.info("\nStep 3: Evaluation - SKIPPED")

    else:
        logger.info("\nStep 3: Evaluation")
        logger.info("-" * 60)

        try:
            # Get model ID (from arg or metadata)
            if args.model_id:
                eval_model_id = args.model_id
            else:
                # Load from metadata
                metadata = load_json(config.FINETUNING_METADATA_JSON)
                eval_model_id = metadata.get('fine_tuned_model_id')

            if not eval_model_id:
                logger.error("Model ID not found for evaluation")
                return 1

            # Override sys.argv for evaluate module
            original_argv = sys.argv
            sys.argv = ['evaluate.py', '--model-id', eval_model_id]

            # Run evaluate module
            exit_code = evaluate.main()

            # Restore sys.argv
            sys.argv = original_argv

            if exit_code != 0:
                logger.error("Evaluation failed")
                return exit_code

            steps_completed.append("evaluate")
            logger.info("✓ Evaluation completed")

        except Exception as e:
            logger.error(f"Error during evaluation: {e}", exc_info=True)
            return 1

    # ========================================================================
    # Pipeline Summary
    # ========================================================================

    pipeline_end = datetime.now()
    duration = (pipeline_end - pipeline_start).total_seconds()

    logger.info("\n" + "="*60)
    logger.info("Pipeline Execution Summary")
    logger.info("="*60)
    logger.info(f"Start time: {pipeline_start.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"End time: {pipeline_end.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Duration: {duration/60:.1f} minutes")
    logger.info(f"Steps completed: {', '.join(steps_completed)}")

    # Generate summary report
    summary_lines = []
    summary_lines.append("# Fine-Tuning Pipeline Execution Summary")
    summary_lines.append("")
    summary_lines.append(f"**Execution Date**: {pipeline_start.strftime('%Y-%m-%d %H:%M:%S')}")
    summary_lines.append(f"**Duration**: {duration/60:.1f} minutes")
    summary_lines.append("")
    summary_lines.append("## Steps Completed")
    summary_lines.append("")
    for step in steps_completed:
        summary_lines.append(f"- {step}")
    summary_lines.append("")

    # Add evaluation metrics if available
    if config.METRICS_JSON.exists():
        logger.info("\nLoading evaluation metrics...")
        metrics = load_json(config.METRICS_JSON)

        summary_lines.append("## Results")
        summary_lines.append("")
        summary_lines.append(f"**Model ID**: `{metrics.get('model_id', 'N/A')}`")
        summary_lines.append(f"**Overall Accuracy**: {metrics.get('overall_accuracy', 0):.4f}")
        summary_lines.append(f"**Current Stance Accuracy**: {metrics['stance_current'].get('accuracy', 0):.4f}")
        summary_lines.append(f"**Future Stance Accuracy**: {metrics['stance_future'].get('accuracy', 0):.4f}")
        summary_lines.append("")

        logger.info(f"Model ID: {metrics.get('model_id', 'N/A')}")
        logger.info(f"Overall Accuracy: {metrics.get('overall_accuracy', 0):.4f}")

    summary_lines.append("## Output Files")
    summary_lines.append("")
    summary_lines.append(f"- Training data: `{config.TRAIN_JSONL}`")
    summary_lines.append(f"- Test data: `{config.TEST_JSONL}`")
    summary_lines.append(f"- Fine-tuning metadata: `{config.FINETUNING_METADATA_JSON}`")
    summary_lines.append(f"- Evaluation report: `{config.EVALUATION_REPORT_MD}`")
    summary_lines.append(f"- Predictions: `{config.PREDICTIONS_CSV}`")
    summary_lines.append("")

    # Save summary
    with open(config.PIPELINE_SUMMARY_MD, 'w') as f:
        f.write("\n".join(summary_lines))

    logger.info(f"\nSummary saved to: {config.PIPELINE_SUMMARY_MD}")

    logger.info("\n" + "="*60)
    logger.info("✓ Pipeline completed successfully!")
    logger.info("="*60)

    return 0


# ============================================================================
# Argument Parsing
# ============================================================================

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for pipeline orchestrator.

    Returns:
        Parsed arguments namespace with the following attributes:
        Step control:
        - skip_prepare: Skip data preparation step
        - skip_finetune: Skip fine-tuning step
        - skip_evaluate: Skip evaluation step
        - dry_run: Only prepare data (no fine-tuning or evaluation)

        Model specification:
        - model_id: Fine-tuned model ID (optional)

        Hyperparameters:
        - n_epochs: Number of training epochs
        - learning_rate_multiplier: Learning rate multiplier
        - suffix: Model name suffix
    """
    parser = argparse.ArgumentParser(
        description="Run complete fine-tuning pipeline for GPT-5-mini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline
  python run_pipeline.py

  # Skip data preparation (use existing files)
  python run_pipeline.py --skip-prepare

  # Dry run (prepare data only)
  python run_pipeline.py --dry-run

  # Resume from fine-tuning
  python run_pipeline.py --skip-prepare --skip-finetune --model-id ft:gpt-5-mini:xxx

  # Custom hyperparameters
  python run_pipeline.py --n-epochs 5 --learning-rate-multiplier 1.5
        """
    )

    # Step control
    parser.add_argument(
        '--skip-prepare',
        action='store_true',
        help='Skip data preparation (use existing JSONL files)'
    )
    parser.add_argument(
        '--skip-finetune',
        action='store_true',
        help='Skip fine-tuning (use existing model)'
    )
    parser.add_argument(
        '--skip-evaluate',
        action='store_true',
        help='Skip evaluation'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Prepare data only, do not fine-tune or evaluate'
    )

    # Model specification
    parser.add_argument(
        '--model-id',
        type=str,
        help='Fine-tuned model ID (for evaluation with --skip-finetune)'
    )

    # Hyperparameters
    parser.add_argument(
        '--n-epochs',
        type=int,
        help=f'Number of training epochs (default: {config.N_EPOCHS})'
    )
    parser.add_argument(
        '--learning-rate-multiplier',
        type=float,
        help='Learning rate multiplier (default: auto)'
    )
    parser.add_argument(
        '--suffix',
        type=str,
        default='monetary-stance',
        help='Model name suffix (default: monetary-stance)'
    )

    return parser.parse_args()


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main execution pipeline."""
    # Parse command-line arguments
    args = parse_arguments()

    # Setup logging
    logger = setup_logging(config.LOG_DIR, "run_pipeline")

    try:
        exit_code = run_complete_pipeline(args, logger)
        sys.exit(exit_code)

    except KeyboardInterrupt:
        logger.warning("\nPipeline interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
