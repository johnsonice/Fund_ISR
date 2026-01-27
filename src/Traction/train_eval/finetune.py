"""
Fine-tune GPT model for stance/agreement classification.

Supports: monetary_stance, fiscal_stance, monetary_agreement, fiscal_agreement
"""
#%%
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from tqdm import tqdm
import training_config as config
sys.path.insert(0, str(config.PROJECT_ROOT))
from training_utils import setup_logging, load_openai_client, save_json, check_finetuning_dataset


def upload_training_file(file_path: Path, client, logger) -> str:
    """Upload JSONL to OpenAI Files API."""
    logger.info(f"Uploading training file: {file_path}")
    logger.info(f"File size: {file_path.stat().st_size / 1024:.2f} KB")

    with open(file_path, 'rb') as f:
        response = client.files.create(file=f, purpose='fine-tune')

    logger.info(f"✓ File uploaded: {response.id}")
    return response.id


def create_finetuning_job(
    file_id: str,
    model: str,
    hyperparams: Dict[str, Any],
    client,
    logger,
    suffix: Optional[str] = None,
) -> str:
    """Create fine-tuning job with OpenAI API."""
    logger.info(f"Creating fine-tuning job (model: {model})")

    # Build job parameters
    job_params = {'training_file': file_id, 'model': model}

    # Add non-auto hyperparameters
    job_hyperparams = {
        k: v for k, v in hyperparams.items()
        if v is not None and v != 'auto'
    }
    if job_hyperparams:
        job_params['hyperparameters'] = job_hyperparams

    if suffix:
        job_params['suffix'] = suffix[:18]

    response = client.fine_tuning.jobs.create(**job_params)
    logger.info(f"✓ Job created: {response.id} (status: {response.status})")
    return response.id


def monitor_job_status(job_id: str, client, logger, poll_interval: int = 60) -> Dict[str, Any]:
    """Poll job status until completion."""
    logger.info(f"Monitoring job {job_id} (poll: {poll_interval}s)")
    logger.info("This may take 10-40 minutes...")

    start_time = time.time()
    last_status = None

    with tqdm(desc="Fine-tuning", unit="check", bar_format='{desc}: {elapsed}') as pbar:
        while True:
            job = client.fine_tuning.jobs.retrieve(job_id)

            if job.status != last_status:
                logger.info(f"[{time.time() - start_time:.0f}s] Status: {job.status}")
                last_status = job.status

            pbar.set_description(f"Fine-tuning ({job.status})")
            pbar.update(1)

            if job.status in ['succeeded', 'failed', 'cancelled']:
                break

            time.sleep(poll_interval)

    # Log final status
    elapsed = (time.time() - start_time) / 60
    logger.info(f"Job finished: {job.status} ({elapsed:.1f} min)")

    if job.status == 'succeeded':
        logger.info(f"✓ Model: {job.fine_tuned_model}")
    elif job.status == 'failed':
        logger.error(f"✗ Failed: {getattr(job, 'error', 'unknown')}")

    return {
        'id': job.id,
        'status': job.status,
        'model': job.model,
        'fine_tuned_model': getattr(job, 'fine_tuned_model', None),
        'training_file': job.training_file,
        'trained_tokens': getattr(job, 'trained_tokens', None),
        'created_at': job.created_at,
        'finished_at': getattr(job, 'finished_at', None),
        'hyperparameters': job.hyperparameters.to_dict() if hasattr(job, 'hyperparameters') else {},
        'error': job.error.to_dict() if getattr(job, 'error', None) else None,
    }


def save_job_metadata(job_details: Dict[str, Any], hyperparams: Dict[str, Any], output_path: Path, logger):
    """Save fine-tuning metadata as JSON."""
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
    }
    save_json(metadata, output_path)
    logger.info(f"✓ Metadata saved: {output_path}")


def run_finetuning_pipeline(
    train_file: Path,
    hyperparams: Dict[str, Any],
    client,
    logger,
    model: str = config.BASE_MODEL,
    suffix: Optional[str] = None,
    metadata_path: Optional[Path] = None,
) -> str:
    """Run end-to-end fine-tuning pipeline. Returns fine-tuned model ID."""
    check_finetuning_dataset(train_file)
    file_id = upload_training_file(train_file, client, logger)

    job_id = create_finetuning_job(
        file_id=file_id,
        model=model,
        hyperparams=hyperparams,
        client=client,
        logger=logger,
        suffix=suffix,
    )

    job_details = monitor_job_status(
        job_id=job_id,
        client=client,
        logger=logger,
        poll_interval=config.JOB_POLL_INTERVAL,
    )

    if metadata_path:
        save_job_metadata(job_details, hyperparams, metadata_path, logger)

    if job_details['status'] == 'succeeded':
        return job_details['fine_tuned_model']
    raise RuntimeError(f"Job {job_id} failed: {job_details['status']}")


def parse_arguments(args=None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Fine-tune GPT for stance/agreement classification")
    parser.add_argument('--task-type', choices=config.TASK_TYPES, default=config.DEFAULT_TASK_TYPE,
                        help='Task type (default: monetary_stance)')
    parser.add_argument('--model', type=str, default=config.BASE_MODEL,
                        help=f'Base model to fine-tune (default: {config.BASE_MODEL})')
    parser.add_argument('--train-file', type=Path, default=None,
                        help='Training JSONL file (default: task-specific)')
    parser.add_argument('--n-epochs', type=int, default=config.N_EPOCHS,
                        help='Number of training epochs')
    parser.add_argument('--batch-size', default=config.BATCH_SIZE,
                        help='Batch size (default: auto)')
    parser.add_argument('--learning-rate-multiplier', type=float, default=None,
                        help='Learning rate multiplier (default: auto)')
    parser.add_argument('--suffix', type=str, default=None,
                        help='Model suffix (max 18 chars, default: task-type)')
    return parser.parse_args(args)

#%%
def main():
    """Main entry point."""
    args = parse_arguments()
    logger = setup_logging(config.LOG_DIR, "finetune")

    logger.info(f"{'='*60}")
    logger.info(f"Fine-tuning: {args.task_type}")
    logger.info(f"{'='*60}")

    try:
        # Get task config and resolve paths
        task_config = config.get_task_config(args.task_type)
        output_dir = task_config['output_dir']
        train_file = args.train_file or (output_dir / f"train_{args.task_type}.jsonl")
        metadata_file = output_dir / f"finetuning_metadata_{args.task_type}.json"
        suffix = args.suffix or args.task_type.replace('_', '-')

        if not train_file.exists():
            raise FileNotFoundError(
                f"Training file not found: {train_file}\n"
                f"Run: python prepare_data.py --task-type {args.task_type}"
            )

        hyperparams = {
            'n_epochs': args.n_epochs,
            'batch_size': args.batch_size,
            'learning_rate_multiplier': args.learning_rate_multiplier or config.LEARNING_RATE_MULTIPLIER,
        }

        model_id = run_finetuning_pipeline(
            train_file=train_file,
            hyperparams=hyperparams,
            client=load_openai_client(),
            logger=logger,
            model=args.model,
            suffix=suffix,
            metadata_path=metadata_file,
        )

        logger.info(f"{'='*60}")
        logger.info(f"✓ Complete! Model: {model_id}")
        logger.info(f"Next: python evaluate.py --task-type {args.task_type} --model-id {model_id}")
        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    main()
