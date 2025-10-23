"""
Fine-tuning pipeline for GPT-5-mini monetary stance classification.

This package provides a complete pipeline for:
1. Data preparation (Excel → OpenAI JSONL format)
2. Model fine-tuning (OpenAI API)
3. Evaluation (comprehensive metrics)

Modules:
- training_config: Configuration and paths
- training_utils: Shared utility functions
- prepare_data: Data preparation script
- finetune: Fine-tuning orchestration
- evaluate: Model evaluation
- run_pipeline: End-to-end pipeline orchestrator
"""

__version__ = "1.0.0"
__author__ = "IMF Traction Project"

# Make key functions available at package level
from . import training_config
from . import training_utils
