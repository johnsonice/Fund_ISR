"""
Fine-tuning orchestration script for GPT-5-mini.

Uploads training data to OpenAI and manages the fine-tuning job lifecycle.
"""
#%%
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from tqdm import tqdm

# Add project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import training_config as config
from training_utils import (
    setup_logging,
    load_openai_client,
    save_json,
    load_json,
)


# ============================================================================
# File Upload
# ============================================================================

def upload_training_file(file_path: Path, client, logger) -> str:
    """
    Upload JSONL to OpenAI Files API.

    Args:
        file_path: Path to training JSONL file
        client: OpenAI client instance
        logger: Logger instance

    Returns:
        file_id: OpenAI file ID
    """
    logger.info(f"Uploading training file: {file_path}")
    logger.info(f"File size: {file_path.stat().st_size / 1024:.2f} KB")

    with open(file_path, 'rb') as f:
        response = client.files.create(
            file=f,
            purpose='fine-tune'
        )

    file_id = response.id
    logger.info(f"✓ File uploaded successfully: {file_id}")

    return file_id


# ============================================================================
# Fine-Tuning Job
# ============================================================================

def create_finetuning_job(
    file_id: str,
    model: str,
    hyperparams: Dict[str, Any],
    client,
    logger,
    suffix: Optional[str] = None,
) -> str:
    """
    Create fine-tuning job with OpenAI API.

    Args:
        file_id: Training file ID
        model: Base model name (e.g., 'gpt-5-mini-2025-08-07')
        hyperparams: Hyperparameters dict (n_epochs, batch_size, learning_rate_multiplier)
        client: OpenAI client instance
        logger: Logger instance
        suffix: Optional suffix for model name (max 18 chars)

    Returns:
        job_id: Fine-tuning job ID
    """
    logger.info(f"Creating fine-tuning job...")
    logger.info(f"  Base model: {model}")
    logger.info(f"  Training file: {file_id}")
    logger.info(f"  Hyperparameters: {hyperparams}")

    # Build hyperparameters for API
    job_hyperparams = {}

    if hyperparams.get('n_epochs') and hyperparams['n_epochs'] != 'auto':
        job_hyperparams['n_epochs'] = hyperparams['n_epochs']

    if hyperparams.get('batch_size') and hyperparams['batch_size'] != 'auto':
        job_hyperparams['batch_size'] = hyperparams['batch_size']

    if hyperparams.get('learning_rate_multiplier') and hyperparams['learning_rate_multiplier'] != 'auto':
        job_hyperparams['learning_rate_multiplier'] = hyperparams['learning_rate_multiplier']

    # Create job
    job_params = {
        'training_file': file_id,
        'model': model,
    }

    if job_hyperparams:
        job_params['hyperparameters'] = job_hyperparams

    if suffix:
        job_params['suffix'] = suffix[:18]  # Max 18 chars

    response = client.fine_tuning.jobs.create(**job_params)

    job_id = response.id
    logger.info(f"✓ Fine-tuning job created: {job_id}")
    logger.info(f"  Status: {response.status}")

    return job_id


def monitor_job_status(
    job_id: str,
    client,
    logger,
    poll_interval: int = 60,
) -> Dict[str, Any]:
    """
    Monitor job with progress updates.

    Polls job status until completion (succeeded/failed/cancelled).
    Displays: queued → running → succeeded/failed

    Args:
        job_id: Fine-tuning job ID
        client: OpenAI client instance
        logger: Logger instance
        poll_interval: Seconds between status checks

    Returns:
        Final job details dictionary
    """
    logger.info(f"Monitoring job: {job_id}")
    logger.info(f"Poll interval: {poll_interval}s")
    logger.info("This may take 10-40 minutes depending on queue and dataset size...")

    start_time = time.time()
    last_status = None

    with tqdm(desc="Fine-tuning", unit="check", bar_format='{desc}: {elapsed}') as pbar:
        while True:
            # Get job status
            job = client.fine_tuning.jobs.retrieve(job_id)
            status = job.status

            # Log status changes
            if status != last_status:
                elapsed = time.time() - start_time
                logger.info(f"[{elapsed:.0f}s] Status: {status}")

                if hasattr(job, 'trained_tokens') and job.trained_tokens:
                    logger.info(f"  Trained tokens: {job.trained_tokens}")

                last_status = status

            # Update progress bar
            pbar.set_description(f"Fine-tuning ({status})")
            pbar.update(1)

            # Check if job finished
            if status in ['succeeded', 'failed', 'cancelled']:
                break

            # Wait before next check
            time.sleep(poll_interval)

    # Log final status
    elapsed = time.time() - start_time
    logger.info(f"\n{'='*60}")
    logger.info(f"Job finished: {status}")
    logger.info(f"Total time: {elapsed/60:.1f} minutes")

    if status == 'succeeded':
        logger.info(f"✓ Fine-tuned model: {job.fine_tuned_model}")
        if hasattr(job, 'trained_tokens') and job.trained_tokens:
            logger.info(f"  Trained tokens: {job.trained_tokens}")
    elif status == 'failed':
        logger.error(f"✗ Job failed")
        if hasattr(job, 'error') and job.error:
            logger.error(f"  Error: {job.error}")
    else:
        logger.warning(f"Job cancelled")

    logger.info(f"{'='*60}\n")

    # Convert job to dict for saving
    job_dict = {
        'id': job.id,
        'status': job.status,
        'model': job.model,
        'fine_tuned_model': job.fine_tuned_model if hasattr(job, 'fine_tuned_model') else None,
        'created_at': job.created_at,
        'finished_at': job.finished_at if hasattr(job, 'finished_at') else None,
        'trained_tokens': job.trained_tokens if hasattr(job, 'trained_tokens') else None,
        'training_file': job.training_file,
        'hyperparameters': job.hyperparameters.to_dict() if hasattr(job, 'hyperparameters') else {},
        'error': job.error.to_dict() if hasattr(job, 'error') and job.error else None,
    }

    return job_dict


# ============================================================================
# Metadata Management
# ============================================================================

def save_job_metadata(
    job_details: Dict[str, Any],
    hyperparams: Dict[str, Any],
    output_path: Path,
    logger,
):
    """
    Save fine-tuning metadata as JSON.

    Args:
        job_details: Job details from OpenAI API
        hyperparams: Input hyperparameters
        output_path: Path to save metadata JSON
        logger: Logger instance
    """
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'job_id': job_details['id'],
        'status': job_details['status'],
        'base_model': job_details['model'],
        'fine_tuned_model_id': job_details.get('fine_tuned_model'),
        'training_file_id': job_details['training_file'],
        'hyperparameters_input': hyperparams,
        'hyperparameters_actual': job_details.get('hyperparameters', {}),
        'trained_tokens': job_details.get('trained_tokens'),
        'created_at': job_details.get('created_at'),
        'finished_at': job_details.get('finished_at'),
        'error': job_details.get('error'),
    }

    logger.info(f"Saving metadata to: {output_path}")
    save_json(metadata, output_path)
    logger.info(f"✓ Metadata saved")


# ============================================================================
# Main Pipeline
# ============================================================================

def run_finetuning_pipeline(
    train_file: Path,
    hyperparams: Dict[str, Any],
    client,
    logger,
    suffix: Optional[str] = None,
) -> str:
    """
    End-to-end fine-tuning pipeline.

    Args:
        train_file: Path to training JSONL file
        hyperparams: Hyperparameters dictionary
        client: OpenAI client instance
        logger: Logger instance
        suffix: Optional model name suffix

    Returns:
        fine_tuned_model_id: ID of the fine-tuned model
    """
    # Upload training file
    file_id = upload_training_file(train_file, client, logger)

    # Create fine-tuning job
    job_id = create_finetuning_job(
        file_id=file_id,
        model=config.BASE_MODEL,
        hyperparams=hyperparams,
        client=client,
        logger=logger,
        suffix=suffix,
    )

    # Monitor job until completion
    job_details = monitor_job_status(
        job_id=job_id,
        client=client,
        logger=logger,
        poll_interval=config.JOB_POLL_INTERVAL,
    )

    # Save metadata
    save_job_metadata(
        job_details=job_details,
        hyperparams=hyperparams,
        output_path=config.FINETUNING_METADATA_JSON,
        logger=logger,
    )

    # Return model ID if successful
    if job_details['status'] == 'succeeded':
        return job_details['fine_tuned_model']
    else:
        raise RuntimeError(f"Fine-tuning job {job_id} did not succeed: {job_details['status']}")


# ============================================================================
# Argument Parsing
# ============================================================================

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for fine-tuning script.

    Returns:
        Parsed arguments namespace with the following attributes:
        - train_file: Path to training JSONL file
        - n_epochs: Number of training epochs
        - batch_size: Batch size (or 'auto')
        - learning_rate_multiplier: Learning rate multiplier (or None for auto)
        - suffix: Model name suffix (max 18 chars)
    """
    parser = argparse.ArgumentParser(
        description="Fine-tune GPT-5-mini for monetary stance classification"
    )
    parser.add_argument(
        '--train-file',
        type=Path,
        default=config.TRAIN_JSONL,
        help='Path to training JSONL file'
    )
    parser.add_argument(
        '--n-epochs',
        type=int,
        default=config.N_EPOCHS,
        help='Number of training epochs (default: auto)'
    )
    parser.add_argument(
        '--batch-size',
        default=config.BATCH_SIZE,
        help='Batch size (default: auto)'
    )
    parser.add_argument(
        '--learning-rate-multiplier',
        type=float,
        default=None,
        help='Learning rate multiplier (default: auto)'
    )
    parser.add_argument(
        '--suffix',
        type=str,
        default='monetary-stance',
        help='Model name suffix (max 18 chars)'
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
    logger = setup_logging(config.LOG_DIR, "finetune")

    logger.info("="*60)
    logger.info("Starting fine-tuning pipeline")
    logger.info("="*60)

    try:
        # Check training file exists
        if not args.train_file.exists():
            raise FileNotFoundError(
                f"Training file not found: {args.train_file}\n"
                f"Please run prepare_data.py first."
            )

        # Setup hyperparameters
        hyperparams = {
            'n_epochs': args.n_epochs,
            'batch_size': args.batch_size,
            'learning_rate_multiplier': args.learning_rate_multiplier or config.LEARNING_RATE_MULTIPLIER,
        }

        # Load OpenAI client
        finetune_client = load_openai_client()

        # Run pipeline
        model_id = run_finetuning_pipeline(
            train_file=args.train_file,
            hyperparams=hyperparams,
            client=finetune_client,
            logger=logger,
            suffix=args.suffix,
        )

        logger.info("="*60)
        logger.info("✓ Fine-tuning completed successfully!")
        logger.info("="*60)
        logger.info(f"Fine-tuned model ID: {model_id}")
        logger.info(f"Metadata saved to: {config.FINETUNING_METADATA_JSON}")
        logger.info("\nNext steps:")
        logger.info(f"  python evaluate.py --model-id {model_id}")

        return 0

    except Exception as e:
        logger.error(f"Error during fine-tuning: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
