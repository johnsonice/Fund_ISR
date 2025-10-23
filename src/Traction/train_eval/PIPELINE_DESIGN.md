# Fine-Tuning Pipeline for GPT-5-mini Monetary Stance Classification

## Overview
Modular pipeline for fine-tuning GPT-5-mini on IMF monetary stance classification using supervised fine-tuning (SFT) with OpenAI API.

## Module Structure

Location: `/data/home/xiong/dev/Fund_ISR/src/Traction/train_eval/`

### 1. `config.py` - Configuration and Constants

**Purpose**: Centralized configuration for all scripts

**Contents**:
- Data paths
  - Training data: `/data/home/xiong/data/Fund/CSR/Traction/output/finetuning/monetary/cv/training_2.xlsx`
  - Testing data: `/data/home/xiong/data/Fund/CSR/Traction/output/finetuning/monetary/cv/testing_2.xlsx`
  - Prompt template: `/data/home/xiong/dev/Fund_ISR/src/Traction/prompts/monetary_stance_simple.md`
  - Output directory: `/data/home/xiong/data/Fund/CSR/Traction/output/finetuning/monetary/cv/`

- Model settings
  - Base model: `gpt-5-mini-2025-08-07` (GPT-5 series, August 2025)
  - Temperature: 0.0 (for evaluation consistency)

- Fine-tuning hyperparameters
  - n_epochs: 3 (default, can be auto-tuned by OpenAI)
  - batch_size: auto (OpenAI determines optimal)
  - learning_rate_multiplier: auto (OpenAI determines optimal)

- Label mappings
  - Current stance labels: ["restrictive", "neutral", "accommodative", "unclear", "irrelevant"]
  - Future stance labels: ["tightening", "tightening bias", "no change", "loosening bias", "loosening", "unclear", "irrelevant"]

---

### 2. `prepare_data.py` - Data Preparation

**Purpose**: Convert Excel data to OpenAI fine-tuning JSONL format

**Key Functions**:

```python
def load_excel_data(file_path: str) -> pd.DataFrame
    """Load and validate Excel file structure"""

def load_prompt_template(template_path: str) -> dict
    """Load monetary_stance_simple.md using libs/prompt_utils.py"""

def create_training_example(row: pd.Series, text_col: str, text_author: str,
                           prompt_template: dict) -> dict
    """
    Create single OpenAI message format example.

    Returns:
    {
      "messages": [
        {"role": "system", "content": "You are an experience macroeconomist..."},
        {"role": "user", "content": "Country: Thailand; Year: 2016\nText: ..."},
        {"role": "assistant", "content": '{"stance_current": "unclear", "stance_future": "loosening bias"}'}
      ]
    }
    """

def prepare_dataset(df: pd.DataFrame, prompt_template: dict,
                   text_author: str, text_col: str,
                   label_current_col: str, label_future_col: str) -> List[dict]
    """
    Generate examples for single author (staff OR buff).

    - text_author: "IMF staff" or "country authority"
    - Fills {TEXT_AUTHOR}, {COUNTRY}, {YEAR}, {TEXT} in prompt
    - KEEPS all labels including "unclear" and "irrelevant"
    - Returns list of message dictionaries
    """

def save_jsonl(examples: List[dict], output_path: str)
    """Write examples to JSONL file"""

def generate_stats_report(train_examples: List[dict], test_examples: List[dict]) -> dict
    """
    Calculate and save dataset statistics:
    - Total examples count
    - Label distributions (current/future stance)
    - Average text length
    - Examples per author type (staff/buff)
    """
```

**Execution Flow**:
1. Load training_2.xlsx and testing_2.xlsx
2. Load monetary_stance_simple.md prompt template
3. **Generate dual examples per row**:
   - One example using "staff" text with staff labels (`staff_stance_current`, `staff_stance_future`)
   - One example using "buff" text with buff labels (`buff_stance_current`, `buff_stance_future`)
   - Text author field: "IMF staff" vs "country authority"
4. Save `train.jsonl` (~462 examples) and `test.jsonl` (~116 examples)
5. Generate `data_stats.json` with label distributions

**Output Files**:
- `train.jsonl` - Training data in OpenAI format
- `test.jsonl` - Test data in OpenAI format
- `data_stats.json` - Statistics report

---

### 3. `finetune.py` - Fine-Tuning Orchestration

**Purpose**: Upload data and manage OpenAI fine-tuning job

**Key Functions**:

```python
def upload_training_file(file_path: str, client: OpenAI) -> str
    """
    Upload JSONL to OpenAI Files API.
    Returns: file_id
    """

def create_finetuning_job(file_id: str, model: str, hyperparams: dict,
                         client: OpenAI) -> str
    """
    Create fine-tuning job with OpenAI API.

    Args:
        hyperparams: {"n_epochs": 3, "batch_size": "auto", ...}

    Returns: job_id
    """

def monitor_job_status(job_id: str, client: OpenAI, poll_interval: int = 60)
    """
    Monitor job with progress updates using tqdm.
    Prints: queued → running → succeeded/failed
    Shows: training loss, validation loss (if available)
    """

def save_job_metadata(job_id: str, model_id: str, hyperparams: dict,
                     output_path: str)
    """
    Save fine-tuning metadata as JSON:
    - job_id
    - fine_tuned_model_id
    - base_model
    - hyperparameters
    - training_file_id
    - timestamp
    - final metrics
    """

def run_finetuning_pipeline(train_file: str, config: dict) -> str
    """End-to-end fine-tuning. Returns fine_tuned_model_id"""
```

**Execution Flow**:
1. Initialize OpenAI client with API key from .env
2. Upload train.jsonl to OpenAI
3. Create fine-tuning job with gpt-5-mini base model
4. Monitor job status with progress bar (typically 10-40 minutes)
5. Retrieve fine-tuned model ID (format: `ft:gpt-5-mini-2025-08-07:org:name:id`)
6. Save metadata to `finetuning_metadata.json`

**Output Files**:
- `finetuning_metadata.json` - Job metadata and model ID

---

### 4. `evaluate.py` - Evaluation and Metrics

**Purpose**: Evaluate fine-tuned model on test set with comprehensive metrics

**Key Functions**:

```python
def run_inference(test_examples: List[dict], model_id: str,
                 client: OpenAI) -> List[dict]
    """
    Run inference on test set.

    - Uses temperature=0 for deterministic outputs
    - Includes retry logic for API errors
    - Progress bar with tqdm
    - Returns predictions with parsed JSON
    """

def parse_predictions(responses: List[str]) -> Tuple[List[str], List[str]]
    """
    Parse assistant JSON responses.

    Returns:
        stance_current_preds, stance_future_preds

    Handles:
    - Malformed JSON (fallback to "error")
    - Missing keys
    - Invalid label values
    """

def calculate_metrics(y_true: List[str], y_pred: List[str],
                     label_name: str) -> dict
    """
    Calculate classification metrics for single task.

    Returns:
    {
      "accuracy": 0.75,
      "precision_macro": 0.72,
      "recall_macro": 0.70,
      "f1_macro": 0.71,
      "f1_weighted": 0.74,
      "confusion_matrix": [[...], ...],
      "classification_report": "..."
    }
    """

def generate_evaluation_report(metrics_current: dict, metrics_future: dict,
                              test_examples: List[dict]) -> str
    """
    Generate markdown evaluation report.

    Includes:
    - Model information
    - Dataset statistics
    - Overall accuracy
    - Per-task metrics (current/future)
    - Confusion matrices (text + visual)
    - Error analysis (top misclassifications)
    - Label-wise performance breakdown
    """

def compare_with_baseline(finetuned_metrics: dict, baseline_model: str = "gpt-5-mini")
    """
    Optional: Run same evaluation on base gpt-5-mini for comparison.
    Shows performance improvement from fine-tuning.
    """
```

**Execution Flow**:
1. Load test.jsonl
2. Load fine-tuned model ID from metadata
3. Run inference on all test examples
4. Parse predictions and handle errors
5. Calculate metrics for both tasks (stance_current, stance_future)
6. Generate confusion matrices using sklearn
7. Compute overall accuracy and per-label F1 scores
8. Create detailed markdown report
9. Save predictions to CSV for manual review

**Output Files**:
- `evaluation_report.md` - Comprehensive metrics report
- `predictions.csv` - All predictions with ground truth for analysis
- `metrics.json` - Raw metrics in JSON format

**Metrics Included**:
- **Overall Accuracy**: % correct on both tasks
- **Per-task Accuracy**: stance_current and stance_future separately
- **F1 Scores**: Macro and weighted for each task
- **Confusion Matrices**: Visual representation of classification errors
- **Label Distribution**: Compare predictions vs ground truth distributions
- **Error Analysis**: Most common misclassifications

---

### 5. `utils.py` - Shared Utilities

**Purpose**: Reusable helper functions across all scripts

**Key Functions**:

```python
def setup_logging(log_dir: str, script_name: str) -> logging.Logger
    """
    Setup logging following existing pattern.
    Format: src/Traction/log/{USER}/{YYYY-MM-DD}/train_eval-{script}-{HH:MM}.log
    """

def validate_dataframe(df: pd.DataFrame, required_cols: List[str])
    """Validate DataFrame has required columns, raise informative errors"""

def load_openai_client() -> OpenAI
    """Load OpenAI client with API key from .env file"""

def load_jsonl(file_path: str) -> List[dict]
    """Read JSONL file into list of dictionaries"""

def save_jsonl(data: List[dict], file_path: str)
    """Write list of dictionaries to JSONL file"""

def format_prompt_with_vars(prompt_template: str, variables: dict) -> str
    """Replace {VARIABLE} placeholders in prompt template"""

def handle_api_error(func, max_retries: int = 3, backoff: float = 2.0)
    """Decorator for retry logic on OpenAI API calls"""

def validate_stance_labels(label: str, valid_labels: List[str]) -> bool
    """Check if label is valid according to schema"""

def create_output_dir(path: str)
    """Create directory if it doesn't exist"""
```

---

### 6. `run_pipeline.py` - End-to-End Execution Script

**Purpose**: Orchestrate full pipeline with single command

**Key Functions**:

```python
def main(args):
    """
    Run complete pipeline:
    1. Prepare data (prepare_data.py)
    2. Fine-tune model (finetune.py)
    3. Evaluate results (evaluate.py)

    Supports:
    - Resuming from checkpoint (skip completed steps)
    - Custom hyperparameters via CLI
    - Dry-run mode (prepare data only)
    """
```

**Command-Line Arguments**:
```bash
python run_pipeline.py \
  --skip-prepare      # Skip data preparation if already done
  --skip-finetune     # Skip fine-tuning (evaluate existing model)
  --model-id <id>     # Use specific fine-tuned model ID
  --n-epochs 3        # Number of training epochs
  --dry-run           # Only prepare data, don't fine-tune
  --output-dir <path> # Custom output directory
```

**Execution Flow**:
1. Check for existing outputs (train.jsonl, metadata.json)
2. Run data preparation (if needed)
3. Run fine-tuning (if needed)
4. Run evaluation
5. Generate final summary report
6. Save all outputs with timestamps

**Output Files**:
- `pipeline_summary.md` - Complete pipeline run summary

---

## Directory Structure After Execution

```
/data/home/xiong/dev/Fund_ISR/src/Traction/train_eval/
├── config.py
├── prepare_data.py
├── finetune.py
├── evaluate.py
├── utils.py
├── run_pipeline.py
└── README.md  # Usage documentation

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

---

## Usage Examples

### Basic Usage (Full Pipeline)
```bash
cd /data/home/xiong/dev/Fund_ISR/src/Traction/train_eval
conda activate traction
python run_pipeline.py
```

### Step-by-Step Execution
```bash
# 1. Prepare data
python prepare_data.py

# 2. Fine-tune (takes 10-40 minutes)
python finetune.py

# 3. Evaluate
python evaluate.py --model-id ft:gpt-5-mini-2025-08-07:org:name:id
```

### Resume from Checkpoint
```bash
# If data already prepared, skip to fine-tuning
python run_pipeline.py --skip-prepare

# If model already fine-tuned, only evaluate
python run_pipeline.py --skip-prepare --skip-finetune --model-id <your-model-id>
```

### Custom Hyperparameters
```bash
python finetune.py --n-epochs 5 --learning-rate-multiplier 1.5
```

---

## Data Format Details

### Input Excel Columns (Required)
- `country`: Country name
- `year`: Year of report
- `staff`: IMF staff text
- `buff`: Country authority text
- `staff_stance_current`: Staff current stance label
- `staff_stance_future`: Staff future stance label
- `buff_stance_current`: Authority current stance label
- `buff_stance_future`: Authority future stance label

### OpenAI JSONL Format
Each line is a JSON object:
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an experience macroeconomist from IMF. Given a piece of text concerning a particular country in a given year written by IMF staff, complete the following two tasks..."
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

---

## Key Design Decisions

1. **All labels included**: "unclear" and "irrelevant" are valid classification targets
2. **Dual examples**: Both staff and authority texts from each row = ~2x data
3. **Simple prompt**: Start with `monetary_stance_simple.md` (no few-shot, no CoT)
4. **Structured JSON output**: Assistant returns valid JSON matching MonetaryStanceResponse schema
5. **Auto hyperparameters**: Let OpenAI determine optimal batch_size and learning_rate (recommended)
6. **Comprehensive evaluation**: Multi-metric assessment beyond just accuracy
7. **Reusable modules**: Each script is independent and can be run separately
8. **Follows existing patterns**: Uses same utilities as `topic_identification_batch.py` and `inference_agreement_stance.py`

---

## Expected Performance

Based on CLAUDE.md evaluation results:
- **Baseline (gpt-5-mini few-shot)**: ~72% agreement, ~65-70% stance
- **Fine-tuned target**: >75% accuracy on both tasks
- **Training time**: 10-40 minutes depending on queue
- **Cost estimate**: ~$0.50-2.00 for fine-tuning 462 examples (pricing subject to change)

---

## Dependencies

All dependencies already in `requirements.txt`:
- pandas
- openpyxl (for Excel reading)
- openai>=1.0.0
- python-dotenv
- pydantic
- scikit-learn (for metrics)
- tqdm (for progress bars)
- frontmatter (for prompt loading)

---

## Future Extensions

1. **Hyperparameter tuning**: Grid search over n_epochs, learning_rate_multiplier
2. **Prompt variants**: Test few_shot and chain_of_thought templates
3. **Cross-validation**: 5-fold CV for robust evaluation
4. **Fiscal stance**: Replicate pipeline for fiscal policy classification
5. **Model comparison**: Compare gpt-5-mini vs gpt-5 fine-tuning
6. **Active learning**: Identify hard examples for targeted labeling

---

## References

- OpenAI Fine-Tuning Guide: https://platform.openai.com/docs/guides/supervised-fine-tuning
- Project CLAUDE.md: Existing evaluation results and best practices
- Existing codebase: `topic_identification_batch.py`, `inference_agreement_stance.py`
