# Fine-Tuning Pipeline for GPT-5-mini - Monetary Stance Classification

A modular pipeline for fine-tuning GPT-5-mini on IMF monetary policy stance classification using supervised fine-tuning (SFT) with OpenAI API.

## Overview

This pipeline fine-tunes GPT-5-mini to classify monetary policy stances from IMF Article IV consultation documents. It processes both IMF staff and country authority texts to predict:

1. **Current monetary stance**: restrictive, neutral, accommodative, unclear, or irrelevant
2. **Future monetary stance direction**: tightening, tightening bias, no change, loosening bias, loosening, unclear, or irrelevant

## Quick Start

### Prerequisites

1. **Environment**: Activate the `traction` conda environment
   ```bash
   conda activate traction
   ```

2. **API Key**: Ensure `OPENAI_API_KEY` is set in `.env` at project root

3. **Data**: Training and test Excel files should be in:
   - `/data/home/xiong/data/Fund/CSR/Traction/output/finetuning/monetary/cv/training_2.xlsx`
   - `/data/home/xiong/data/Fund/CSR/Traction/output/finetuning/monetary/cv/testing_2.xlsx`

### Basic Usage - Full Pipeline

Run the entire pipeline with one command:

```bash
cd /data/home/xiong/dev/Fund_ISR/src/Traction/train_eval
conda activate traction
python run_pipeline.py
```

This will:
1. Prepare training/test data in OpenAI JSONL format (~5 min)
2. Upload data and fine-tune GPT-5-mini (~10-40 min)
3. Evaluate the fine-tuned model and generate reports (~5 min)

### Step-by-Step Usage

If you prefer to run each step separately:

```bash
# Step 1: Prepare data
python prepare_data.py

# Step 2: Fine-tune model (this takes 10-40 minutes)
python finetune.py

# Step 3: Evaluate model
python evaluate.py
```

## Module Descriptions

### 1. `training_config.py`

Configuration file containing all paths, model settings, and hyperparameters.

**Key settings**:
- `BASE_MODEL`: `gpt-5-mini-2025-08-07`
- `N_EPOCHS`: 3 (default, can be auto-tuned by OpenAI)
- `TEMPERATURE`: 0.0 (for deterministic evaluation)

### 2. `training_utils.py`

Shared utility functions used across all modules:
- Logging setup (follows existing pattern: `log/{USER}/{YYYY-MM-DD}/train_eval-{script}-{HH:MM}.log`)
- OpenAI client initialization
- JSONL file I/O
- Prompt template formatting
- API error handling with retry logic

### 3. `prepare_data.py`

Converts Excel data to OpenAI fine-tuning JSONL format.

**What it does**:
- Loads `training_2.xlsx` and `testing_2.xlsx`
- Loads prompt template from `monetary_stance_simple.md`
- Creates **dual examples** from each row:
  - One using IMF staff text with staff stance labels
  - One using country authority text with authority stance labels
- Saves `train.jsonl` (~462 examples) and `test.jsonl` (~116 examples)
- Generates `data_stats.json` with label distributions

**Output**:
```
train.jsonl           # Training data in OpenAI format
test.jsonl            # Test data in OpenAI format
data_stats.json       # Dataset statistics
```

**Usage**:
```bash
python prepare_data.py
```

### 4. `finetune.py`

Uploads training data and manages OpenAI fine-tuning job.

**What it does**:
- Uploads `train.jsonl` to OpenAI Files API
- Creates fine-tuning job with specified hyperparameters
- Monitors job progress with live status updates
- Saves model ID and metadata when complete

**Output**:
```
finetuning_metadata.json   # Job metadata and fine-tuned model ID
```

**Usage**:
```bash
# Basic usage
python finetune.py

# Custom hyperparameters
python finetune.py --n-epochs 5 --learning-rate-multiplier 1.5

# Custom model name suffix
python finetune.py --suffix my-experiment
```

**Arguments**:
- `--train-file`: Path to training JSONL (default: `train.jsonl`)
- `--n-epochs`: Number of training epochs (default: 3)
- `--batch-size`: Batch size (default: auto)
- `--learning-rate-multiplier`: Learning rate multiplier (default: auto)
- `--suffix`: Model name suffix, max 18 chars (default: `monetary-stance`)

### 5. `evaluate.py`

Evaluates fine-tuned model on test set with comprehensive metrics.

**What it does**:
- Loads test examples from `test.jsonl`
- Runs inference on fine-tuned model (temperature=0)
- Parses JSON predictions and validates format
- Calculates metrics for both tasks (current stance, future stance)
- Generates detailed markdown report with confusion matrices
- Saves predictions to CSV for manual review

**Output**:
```
evaluation_report.md   # Comprehensive metrics report
predictions.csv        # All predictions with ground truth
metrics.json           # Raw metrics in JSON format
```

**Metrics included**:
- Overall accuracy (average of both tasks)
- Per-task accuracy (current stance, future stance)
- F1 scores (macro and weighted)
- Confusion matrices
- Per-label precision, recall, F1
- Classification reports

**Usage**:
```bash
# Automatic (uses model ID from metadata)
python evaluate.py

# Specify model ID explicitly
python evaluate.py --model-id ft:gpt-5-mini-2025-08-07:org:name:id

# Custom test file
python evaluate.py --test-file /path/to/test.jsonl
```

**Arguments**:
- `--model-id`: Fine-tuned model ID (optional, loads from metadata if not specified)
- `--test-file`: Path to test JSONL (default: `test.jsonl`)

### 6. `run_pipeline.py`

Orchestrates the complete pipeline with checkpoint support.

**What it does**:
- Runs all three steps: prepare → finetune → evaluate
- Supports skipping completed steps
- Generates pipeline execution summary
- Tracks execution time and outputs

**Output**:
```
pipeline_summary.md    # Complete pipeline execution summary
```

**Usage**:
```bash
# Run full pipeline
python run_pipeline.py

# Skip data preparation (use existing JSONL files)
python run_pipeline.py --skip-prepare

# Dry run (prepare data only, don't fine-tune)
python run_pipeline.py --dry-run

# Resume from fine-tuning (if model already trained)
python run_pipeline.py --skip-prepare --skip-finetune --model-id ft:gpt-5-mini:xxx

# Custom hyperparameters
python run_pipeline.py --n-epochs 5 --learning-rate-multiplier 1.5
```

**Arguments**:
- `--skip-prepare`: Skip data preparation
- `--skip-finetune`: Skip fine-tuning (use existing model)
- `--skip-evaluate`: Skip evaluation
- `--dry-run`: Prepare data only, don't fine-tune
- `--model-id`: Fine-tuned model ID (for evaluation with `--skip-finetune`)
- `--n-epochs`: Number of training epochs
- `--learning-rate-multiplier`: Learning rate multiplier
- `--suffix`: Model name suffix

## Data Format

### Input Excel Format

Each row in `training_2.xlsx` and `testing_2.xlsx` contains:

| Column | Description |
|--------|-------------|
| `country` | Country name |
| `year` | Year of report |
| `staff` | IMF staff text |
| `buff` | Country authority text |
| `staff_stance_current` | Staff's assessment of current stance |
| `staff_stance_future` | Staff's recommended future direction |
| `buff_stance_current` | Authority's current stance |
| `buff_stance_future` | Authority's planned future direction |

### OpenAI JSONL Format

Each line in `train.jsonl` and `test.jsonl` is a JSON object:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an experience macroeconomist from IMF..."
    },
    {
      "role": "user",
      "content": "Country: Thailand; Year: 2016\nText:\n36. Thailand remains resilient..."
    },
    {
      "role": "assistant",
      "content": "{\"stance_current\": \"unclear\", \"stance_future\": \"loosening bias\"}"
    }
  ]
}
```

## Output Files

After running the full pipeline, you'll have:

```
/data/home/xiong/data/Fund/CSR/Traction/output/finetuning/monetary/cv/
├── train.jsonl                    # Training data (462 examples)
├── test.jsonl                     # Test data (116 examples)
├── data_stats.json                # Dataset statistics
├── finetuning_metadata.json       # Fine-tuning job info
├── evaluation_report.md           # Evaluation metrics
├── predictions.csv                # Model predictions
├── metrics.json                   # Raw metrics
└── pipeline_summary.md            # Full run summary
```

## Expected Performance

Based on CLAUDE.md evaluation results:

- **Baseline (gpt-5-mini few-shot)**: ~72% agreement, ~65-70% stance
- **Fine-tuned target**: >75% accuracy on both tasks
- **Training time**: 10-40 minutes (depends on OpenAI queue)
- **Cost estimate**: ~$0.50-2.00 for fine-tuning 462 examples (pricing subject to change)

## Troubleshooting

### Issue: "OPENAI_API_KEY not found"
**Solution**: Ensure `.env` file exists at project root with:
```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### Issue: "Training file not found"
**Solution**: Run `prepare_data.py` first to generate JSONL files.

### Issue: "Metadata not found"
**Solution**: Run `finetune.py` first, or specify `--model-id` explicitly.

### Issue: "Fine-tuning job failed"
**Solution**: Check the error in logs and `finetuning_metadata.json`. Common issues:
- Invalid JSONL format (run `prepare_data.py` again)
- Insufficient API credits
- Training data too small (should be >10 examples)

### Issue: Parse errors during evaluation
**Solution**: The model may occasionally return malformed JSON. These are tracked separately in metrics. If >5% parse errors, consider:
- Re-running fine-tuning with more epochs
- Using a different prompt template
- Checking if training data has similar issues

## Advanced Usage

### Cross-Validation

To run 5-fold cross-validation:

1. Split your Excel data into 5 folds manually
2. Run pipeline for each fold:
   ```bash
   for fold in {1..5}; do
     python run_pipeline.py --suffix fold-$fold
   done
   ```
3. Average metrics across folds

### Hyperparameter Tuning

Test different hyperparameters:

```bash
# More epochs
python finetune.py --n-epochs 5

# Higher learning rate
python finetune.py --learning-rate-multiplier 2.0

# Combination
python finetune.py --n-epochs 5 --learning-rate-multiplier 1.5
```

### Comparing Prompt Templates

To test different prompts (e.g., few-shot, chain-of-thought):

1. Update `PROMPT_TEMPLATE_PATH` in `training_config.py`
2. Run full pipeline
3. Compare evaluation results

## Logs

All scripts create timestamped logs in:
```
/data/home/xiong/dev/Fund_ISR/src/Traction/log/{USER}/{YYYY-MM-DD}/
├── train_eval-prepare_data-{HH:MM}.log
├── train_eval-finetune-{HH:MM}.log
├── train_eval-evaluate-{HH:MM}.log
└── train_eval-run_pipeline-{HH:MM}.log
```

## Dependencies

All required packages are in `requirements.txt`:
- `pandas` - Data manipulation
- `openpyxl` - Excel reading
- `openai>=1.0.0` - OpenAI API client
- `python-dotenv` - Environment variables
- `pydantic` - Data validation
- `scikit-learn` - Metrics calculation
- `tqdm` - Progress bars
- `frontmatter` - Prompt template parsing

## Design Decisions

1. **All labels included**: "unclear" and "irrelevant" are valid targets (no filtering)
2. **Dual examples**: Each row generates 2 examples (staff + authority) → ~2x data
3. **Simple prompt**: Uses `monetary_stance_simple.md` (no few-shot or chain-of-thought)
4. **Structured output**: Assistant returns JSON matching `MonetaryStanceResponse` schema
5. **Auto hyperparameters**: Lets OpenAI determine optimal batch size and learning rate
6. **Comprehensive evaluation**: Multi-metric assessment beyond accuracy

## Future Extensions

1. **Hyperparameter grid search**: Automated tuning over n_epochs, learning_rate
2. **Prompt variants**: Test few_shot and chain_of_thought templates
3. **Cross-validation**: 5-fold CV for robust evaluation
4. **Fiscal stance**: Replicate pipeline for fiscal policy classification
5. **Model comparison**: Compare gpt-5-mini vs gpt-5 fine-tuning
6. **Active learning**: Identify hard examples for targeted labeling

## References

- [OpenAI Fine-Tuning Guide](https://platform.openai.com/docs/guides/supervised-fine-tuning)
- Project `CLAUDE.md`: Existing evaluation results and best practices
- Existing codebase: `topic_identification_batch.py`, `inference_agreement_stance.py`

## Contact

For issues or questions, refer to project documentation or check existing logs.

## Model fintuning references
- https://cookbook.openai.com/examples/chat_finetuning_data_prep
- https://cookbook.openai.com/examples/fine_tuning_direct_preference_optimization_guide