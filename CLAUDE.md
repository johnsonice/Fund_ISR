# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What's New (Latest Updates)

**Recent Changes (Jan 2026):**
- Updated fiscal domain processing in `inference_agreement_stance.py` (Jan 4, 2026)
- Enhanced visualization charts and post-estimation analysis (Dec 11, 2025)
- Optimized stance prediction pipeline with improved message formatting (Dec 11, 2025)
- Added comprehensive evaluation results comparing GPT-5/5-mini/5-nano models

**Major additions to the repository:**

1. **Production Stance & Agreement Inference** (`src/Traction/inference_agreement_stance.py`)
   - Unified CLI for monetary/fiscal stance and agreement classification
   - OpenAI Batch API integration for cost-effective large-scale processing
   - Supports 4 prompt variants (simple, with_definitions, few_shot, chain_of_thought)
   - Three-step workflow: JSONL generation → batch submission → result post-processing

2. **Post-Estimation Analysis Toolkit** (`src/Traction/post_estimate_analysis/`)
   - `data_vis_utils.py`: Production-ready visualization utilities
   - `data_vis.ipynb`: Comprehensive analysis notebook
   - Income group classification (AE/EM/LC)
   - Agreement trend analysis with disagreement area extraction
   - IMF vs authority stance comparison charts

3. **Enhanced LLM Processing Utilities** (`src/Traction/llm_batch_process_utils.py`)
   - Flexible message building for multi-column DataFrame inputs
   - Safe placeholder formatting (avoids conflicts with JSON in prompts)
   - Supports both simple (single text) and complex (multi-field) prompt templates

4. **Expanded Schema & Prompt Library** (`src/Traction/prompts/`)
   - 17+ prompt templates for stance/agreement tasks
   - Complete Pydantic schema coverage for all tasks
   - PROMPT_REGISTRY for centralized prompt management

**Key improvements:**
- Complete end-to-end pipeline: XML → inference → visualization
- Modular CLI design with subcommand pattern
- Sector-agnostic analysis utilities (reusable across monetary/fiscal)
- Comprehensive evaluation notebooks and demos

## Environment Setup

**Conda Environment:**
- This project uses a conda environment named `traction`
- Always activate the `traction` environment before running any commands: `conda activate traction`
- When installing Python dependencies, use `python -m pip` instead of bare `pip`

**API Keys:**
- OpenAI API key must be set in `.env` file at project root: `OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx`
- The `.env` file is loaded by scripts using `python-dotenv`

**Dependencies:**
```bash
pip install -r requirements.txt
```

## Common Commands

### Data Processing Pipeline

1. **Extract and preprocess XML documents:**
   ```bash
   python src/Traction/data_preprocess.py
   ```
   - Parses Article IV XML documents from `results_v2/` and `results_v5/` folders
   - Outputs: `df_aiv.csv` (document-level), `df_paragraphs.csv` (paragraph-level)

2. **Classify topics (choose one method):**

   **Option A - Async processing (faster for small batches):**
   ```bash
   python src/Traction/topic_identification.py
   # Test mode (sample data):
   python src/Traction/topic_identification.py --test-mode
   ```

   **Option B - Batch processing (cost-effective for large datasets):**
   ```bash
   python src/Traction/topic_identification_batch.py
   ```

3. **Aggregate results to document level:**
   ```bash
   python src/Traction/paragraph_back2_doc.py
   ```

### Stance & Agreement Classification (Production Pipeline)

**Production script**: `src/Traction/inference_agreement_stance.py`

This unified script supports both agreement detection and stance classification using OpenAI Batch API:

```bash
# Agreement classification (monetary or fiscal)
python src/Traction/inference_agreement_stance.py agreement \
  --domain monetary \
  --data-file /path/to/document_by_type_sector.csv \
  --submit \
  --post-process

# Stance classification (monetary or fiscal)
python src/Traction/inference_agreement_stance.py stance \
  --domain monetary \
  --data-file /path/to/document_by_type_sector.csv \
  --submit \
  --post-process

# Test mode (sample 1000 rows)
python src/Traction/inference_agreement_stance.py agreement \
  --domain fiscal \
  --test-mode \
  --submit \
  --post-process

# Advanced: Custom model and prompt variant
python src/Traction/inference_agreement_stance.py stance \
  --domain fiscal \
  --model gpt-5-mini \
  --prompt-variant few_shot \
  --submit \
  --post-process
```

**Key features:**
- Supports both `agreement` and `stance` tasks with `--domain monetary|fiscal`
- Uses OpenAI Batch API for cost-effective processing
- Flexible prompt selection via `--prompt-variant` (simple, with_definitions, few_shot, chain_of_thought)
- Test mode with `--test-mode` (samples 1000 rows by default)
- Three-step workflow: create JSONL → submit batch → post-process results
- Outputs: `agreement_{domain}_results.csv` or `stance_{domain}_results.csv`

**Agreement task specifics:**
- Pivots long-format data (staff/authority rows) to wide format (staff and authority columns side-by-side)
- Requires `type` column (staff/buff) and `text` column
- Output includes agreement classification and disagreement areas

**Stance task specifics:**
- Per-row classification (each text gets its own stance label)
- Normalizes author labels: "staff" → "IMF staff", "buff" → "country authority"
- Output includes `stance_current` and `stance_future` for each row

### Post-Estimation Analysis & Visualization

**Location**: `src/Traction/post_estimate_analysis/`

After running stance/agreement inference, use these tools for analysis:

**Key modules:**
- `data_vis_utils.py`: Reusable visualization utilities (sector-agnostic design)
- `data_vis.ipynb`: Interactive analysis notebook with comprehensive charts

**Key capabilities:**
1. **Income group classification**: Auto-classify countries into AE (advanced economies), EM (emerging markets), LC/LIC (low-income)
2. **Agreement analysis**:
   - Compute "no disagreement" proportions by year and income group
   - Trend analysis of disagreement areas (e.g., inflation targets, interest rate timing)
   - Category extraction from disagreement text fields
3. **Stance analysis**:
   - Pivot stance data to wide format (IMF vs authority comparison)
   - Compute stance direction scores (loosening/tightening scale)
   - Stacked proportion charts showing IMF advice vs authority policy direction
4. **Report counting**: Track Article IV report volumes by year and income group

**Example usage (in notebook):**
```python
from data_vis_utils import (
    filter_year_range,
    add_no_disagreement_flag,
    compute_no_disagreement_proportions_by_year,
    plot_group_lines_by_year,
    pivot_stance_wide,
    compute_imf_vs_authority_share,
    plot_stacked_proportions_by_year
)

# Load results
df = pd.read_csv('agreement_monetary_results.csv')

# Add income groups
df['income_group'] = df['country'].apply(classify_income_group_from_country_name)

# Compute and plot agreement trends
df = add_no_disagreement_flag(df, agreement_col='agreement')
proportions = compute_no_disagreement_proportions_by_year(df, groups=['ALL', 'AE', 'EM', 'LIC'])
plot_group_lines_by_year(proportions, groups=['ALL', 'AE', 'EM', 'LIC'])
```

### Evaluation & Development

- **Evaluation Pipeline**: `notebooks/Traction/evaluate_fiscal_monetray_pipeline.ipynb`
  - Function: `evaluate_prompt_and_model(prompt_key, model_name, data_dir, use_full_dataset=True)`
  - Supports monetary/fiscal stance and agreement tasks
  - Comprehensive evaluation results in `src/Traction/evaluation_results.md`
  - Quick evaluation summary in `src/Traction/temp/temp_eval.md`
- **Inference Demos**:
  - `llm_fiscal_monetary_inference_demo.ipynb`: End-to-end inference examples
  - `llm_fiscal_monetary_eval_demo.ipynb`: Evaluation workflow demonstrations
  - `llm_topic_identification_demo.ipynb`: Topic classification examples
- Run Jupyter notebooks from `notebooks/Traction/` for demos and experimentation
- Logs are automatically created at: `src/Traction/log/{USER}/{YYYY-MM-DD}/Exp-{HH:MM}.log`

## Architecture Overview

### Directory Structure

- **`libs/`**: Reusable utility modules
  - `llm_factory_openai.py`: OpenAI API wrapper with async batch processing (BatchAsyncLLMAgent)
  - `prompt_utils.py`: Prompt template loader and message formatter
  - `llm_utils*.py`: LLM interaction utilities with retry logic
  - `clean_text_utils.py`, `utils_pdf.py`, `utils.py`: Text/PDF/general utilities

- **`src/Traction/`**: Main processing pipeline for Article IV documents
  - **Data preprocessing:**
    - `data_preprocess.py`: XML → paragraph CSV extraction
    - `paragraph_back2_doc.py`: Paragraph → document-level aggregation
  - **Topic classification:**
    - `topic_identification.py`: Async processing (small batches)
    - `topic_identification_batch.py`: Batch API processing (large datasets)
  - **Stance & agreement inference (PRODUCTION):**
    - `inference_agreement_stance.py`: Unified script for agreement detection and stance classification
    - Supports both monetary and fiscal domains
    - Uses OpenAI Batch API for cost efficiency
  - **Shared utilities:**
    - `llm_batch_process_utils.py`: Message builders and batch processing helpers
    - `config.py`: Cross-platform path configuration
  - **Prompts & schemas:**
    - `prompts/schema.py`: Pydantic models and PROMPT_REGISTRY
    - `prompts/*.md`: Markdown prompt templates (4 variants per task)
  - **Post-estimation analysis:**
    - `post_estimate_analysis/data_vis_utils.py`: Visualization utilities (sector-agnostic)
    - `post_estimate_analysis/data_vis.ipynb`: Interactive analysis notebook
  - **Fine-tuning pipeline:**
    - `train_eval/`: Fine-tuning pipeline for GPT-5-mini stance classification (see Fine-Tuning section)
  - **Legacy & reference code:**
    - `reference_code/`: Legacy scripts from earlier pipeline iterations (1-13 numbered scripts)
    - `temp/`: Temporary scripts and evaluation summaries
    - `scripts/`: Shell scripts for batch execution

- **`src/Others/`**: Experimental scripts and one-off analyses
  - `async_inference.py`: Async inference with vLLM server
  - `process_ram_tables/`: RAM table extraction and processing scripts
  - `eval_topic_identification.py`: Topic classification evaluation
  - `post_process_inference_data.py`: Data post-processing utilities

- **`notebooks/Traction/`**: Jupyter notebooks for development and testing
  - `evaluate_fiscal_monetray_pipeline.ipynb`: Comprehensive evaluation framework
  - `llm_fiscal_monetary_inference_demo.ipynb`: Inference examples
  - `llm_fiscal_monetary_eval_demo.ipynb`: Evaluation demonstrations
  - `llm_topic_identification_demo.ipynb`: Topic classification demos

### Core Pipeline Components

**1. Configuration (`src/Traction/config.py`):**
- Cross-platform path configuration (Windows/Linux)
- Data directory paths differ by OS: Windows uses OneDrive paths, Linux uses `~/dev/Fund/CSR/Tractions/`

**2. Data Preprocessing (`src/Traction/data_preprocess.py`):**
- Parses XML documents using BeautifulSoup
- Extracts: Staff Appraisal, Buff Statement, Staff Report body, Authorities' Views
- Outputs paragraph-level data ready for classification

**3. LLM Batch Processing (`src/Traction/llm_batch_process_utils.py`):**
Shared utilities for converting DataFrames to LLM-ready message batches:
- `_build_batch_messages_from_df()`: Simple text-to-messages conversion
  - Single text column input (e.g., paragraph classification)
  - Supports `{TEXT}` placeholder in prompts
  - Used by `topic_identification*.py`
- `_build_batch_messages_from_df_flexible()`: Multi-column flexible mapping
  - Maps multiple DataFrame columns to template placeholders
  - Supports complex prompts with multiple inputs (e.g., `{STAFF_TEXT}`, `{AUTHORITY_TEXT}`, `{COUNTRY}`, `{YEAR}`)
  - Safe placeholder formatting (avoids conflicts with JSON examples in prompts)
  - Used by `inference_agreement_stance.py`
- `_process_batch_async()`: Async batch inference executor
- `_merge_ids_with_responses()`: Merges API responses with original IDs

**4. Topic Classification:**
- Uses OpenAI LLMs with structured output (Pydantic validation)
- Two implementations: async (`topic_identification.py`) and batch API (`topic_identification_batch.py`)
- Both use shared utilities in `llm_batch_process_utils.py`

**5. Stance & Agreement Inference (`src/Traction/inference_agreement_stance.py`):**
Unified production script with modular design:
- **Task selection**: Agreement vs stance classification via CLI subcommands
- **Domain selection**: Monetary vs fiscal policy via `--domain` flag
- **Data reshaping**:
  - Agreement: `_pivot_agreement_rows()` converts long (staff/buff rows) to wide format
  - Stance: Per-row classification with author normalization
- **Batch workflow**:
  - `_create_batch_jsonl()`: Build OpenAI Batch API JSONL files
  - Reuses batch upload/wait/download from `topic_identification_batch.py`
  - `_post_process_results_jsonl()`: Parse structured responses
- **Prompt selection**: `_select_prompt_and_response()` maps task+domain+variant to prompt files
- **Flexible execution**: Generate JSONL only (offline) or full submit + post-process

**6. Schema & Prompts (`src/Traction/prompts/`):**
- `schema.py`: Pydantic models and PROMPT_REGISTRY mapping prompt keys to files/models
  - **Topic classification:**
    - `TopicResponse`: Topic labels with confidence scores (0-100)
  - **Monetary policy:**
    - `MonetaryStanceResponse`: Current stance (restrictive/neutral/accommodative) + future direction (tightening/loosening)
    - `MonetaryStanceChainOfThoughtResponse`: Adds reasoning field
    - `MonetaryAgreementResponse`: Agreement level + disagreement areas
    - `MonetaryAgreementChainOfThoughtResponse`: Adds reasoning field
  - **Fiscal policy:**
    - `FiscalStanceResponse`: Current stance (contractionary/neutral/expansionary) + future direction
    - `FiscalStanceChainOfThoughtResponse`: Adds reasoning field
    - `FiscalAgreementResponse`: Agreement level + disagreement areas
    - `FiscalAgreementChainOfThoughtResponse`: Adds reasoning field
- **Prompt templates**: Markdown files with 4 variants per task
  - `simple`: Minimal instructions
  - `with_definitions`: Adds detailed category definitions
  - `few_shot`: Includes labeled examples (RECOMMENDED)
  - `chain_of_thought`: Adds reasoning step
- **PROMPT_REGISTRY**: Maps prompt keys to files/models
  - Pattern: `{domain}_{task}_{variant}` (e.g., `monetary_stance_few_shot`)
  - All 17 prompt templates registered for easy access

**7. Post-Processing (`src/Traction/paragraph_back2_doc.py`):**
- Aggregates paragraph-level classifications to document-level summaries
- Creates binary dummy variables for topics with confidence > 30%

**8. Post-Estimation Analysis (`src/Traction/post_estimate_analysis/`):**
- **`data_vis_utils.py`**: Production-ready visualization utilities
  - **Income group classification**: `classify_income_group_from_country_name()`, `classify_income_group_from_code()`
  - **DataFrame utilities**: `filter_year_range()`, `coerce_year_int()`, `compute_year_group_counts()`
  - **Agreement analysis**: `add_no_disagreement_flag()`, `compute_no_disagreement_proportions_by_year()`, `extract_categories_from_text()`
  - **Stance analysis**: `pivot_stance_wide()`, `compute_imf_vs_authority_share()`
  - **Plotting helpers**: `plot_group_lines_by_year()`, `plot_stacked_proportions_by_year()`, `plot_category_trends()`
  - **Design philosophy**: Sector-agnostic, composable functions that return data (not side effects)
- **`data_vis.ipynb`**: Comprehensive analysis notebook demonstrating all utilities

### Topic Classification System

**Six Predefined Categories:**
1. Economic Outlook - GDP, growth, forecasts, recession risks
2. Monetary Policy - Interest rates, inflation, central bank actions
3. Fiscal Stance - Government spending, debt, budget balance
4. Financial Stability - Banking sector, financial risks
5. External Stance - Balance of payments, exchange rates, trade
6. Other - Uncategorized topics

**Classification Flow:**
- Paragraph text → LLM with structured prompt → Pydantic schema validation → Confidence scores (0-100)
- Threshold: Topics with confidence > 30% marked as relevant

### LLM Processing Patterns

**BatchAsyncLLMAgent (`libs/llm_factory_openai.py`):**
- Handles concurrent async API calls with progress tracking
- Supports structured output via Pydantic models
- Built-in retry logic and error handling
- Recommended models: `gpt-5-mini` (recommended default, cost-effective), `gpt-5` (premium, higher accuracy), `gpt-5-nano` (budget)
- Model IDs: `gpt-5-mini-2025-08-07`, `gpt-5-2025-08-07`, `gpt-5-nano-2025-08-07`

**Batch Processing Workflow:**
1. Build batch messages from DataFrame (`_build_batch_messages_from_df`)
2. Submit to OpenAI Batch API
3. Monitor batch status
4. Process results when complete
5. Merge with original IDs (`_merge_ids_with_responses`)

### Data Requirements

External data structure (configured in `config.py`):
```
~/dev/Fund/CSR/Tractions/  (Linux)
├── ArticleIV_xml_updated/
│   ├── results_v2/          # XML documents (earlier version)
│   └── results_v5/          # XML documents (later version)
├── text_collection/
│   └── IMF_Main_MetaData_*.xlsx  # Document metadata
└── output/                  # Generated outputs (auto-created)
```

### Output Files

**After preprocessing:**
- `output/df_aiv.csv`: Document-level metadata
- `output/df_paragraphs.csv`: Paragraph-level text

**After topic classification:**
- `output/paragraph_with_sector.csv` (async) or `output/paragraph_with_sector_batch.csv` (batch)
  - Columns: original data + confidence scores for each topic + binary dummies

**After aggregation:**
- `output/document_by_type_sector.csv`: Document-level topic summaries
  - Input for stance/agreement inference

**After stance/agreement inference:**
- **Batch request files:**
  - `agreement_{domain}_batch.jsonl`: OpenAI Batch API request file for agreement tasks
  - `stance_{domain}_batch.jsonl`: OpenAI Batch API request file for stance tasks
- **Batch results:**
  - `batch_results_{batch_id}_{timestamp}.jsonl`: Raw API responses from completed batch
- **Final outputs:**
  - `agreement_monetary_results.csv`: Monetary agreement classifications
    - Columns: id, Print ISBN, topic, country, year, staff, buff, agreement, disagreement_areas
  - `agreement_fiscal_results.csv`: Fiscal agreement classifications
  - `stance_monetary_results.csv`: Monetary stance classifications
    - Columns: id, Print ISBN, topic, country, year, TEXT_AUTHOR, text, stance_current, stance_future
  - `stance_fiscal_results.csv`: Fiscal stance classifications

**Post-analysis outputs (from data_vis.ipynb):**
- Income group enhanced datasets
- Year-over-year trend tables
- Disagreement category analysis tables

### Complete End-to-End Pipeline Workflow

The repository implements a complete pipeline from raw XML to publication-ready analysis:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: Data Extraction & Preprocessing                                │
├─────────────────────────────────────────────────────────────────────────┤
│ Input:  ArticleIV_xml_updated/results_v*/                               │
│ Script: src/Traction/data_preprocess.py                                 │
│ Output: df_aiv.csv (docs), df_paragraphs.csv (paragraphs)               │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: Topic Classification (Optional)                                │
├─────────────────────────────────────────────────────────────────────────┤
│ Input:  df_paragraphs.csv                                               │
│ Script: topic_identification.py OR topic_identification_batch.py        │
│ Output: paragraph_with_sector.csv (with topic confidence scores)        │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: Document-Level Aggregation                                     │
├─────────────────────────────────────────────────────────────────────────┤
│ Input:  paragraph_with_sector.csv                                       │
│ Script: src/Traction/paragraph_back2_doc.py                             │
│ Output: document_by_type_sector.csv (doc-level summaries)               │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: Stance & Agreement Inference (PRODUCTION)                      │
├─────────────────────────────────────────────────────────────────────────┤
│ Input:  document_by_type_sector.csv                                     │
│ Script: src/Traction/inference_agreement_stance.py                      │
│         - Agreement: monetary/fiscal                                     │
│         - Stance: monetary/fiscal                                        │
│ Output: agreement_{domain}_results.csv, stance_{domain}_results.csv     │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 5: Post-Estimation Analysis & Visualization                       │
├─────────────────────────────────────────────────────────────────────────┤
│ Input:  agreement/stance results CSVs                                   │
│ Tools:  post_estimate_analysis/data_vis_utils.py                        │
│         post_estimate_analysis/data_vis.ipynb                           │
│ Output: - Income group classifications                                  │
│         - Agreement trend charts                                        │
│         - Stance comparison charts (IMF vs authorities)                 │
│         - Disagreement area analysis                                    │
│         - Publication-ready visualizations                              │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key decision points:**
- **Async vs Batch API**: Use async for <5K rows, batch API for larger datasets
- **Prompt variant**: Use `few_shot` (recommended) or fine-tuned models for production
- **Model selection**: `gpt-5-mini` (default), `gpt-5` (premium), or fine-tuned `gpt-5-mini`

### Key Design Patterns

1. **Async Processing:** Uses asyncio and `tqdm.asyncio` for concurrent API calls with progress bars
2. **Structured Output:** All LLM responses validated against Pydantic schemas
3. **Batch API:** Cost-effective processing for large datasets via OpenAI Batch API
4. **Wide Format Conversion:** Pivot long-form results to wide DataFrame with topic columns
5. **Flexible Message Building:** Template-based system supports single or multi-column inputs
6. **Safe Placeholder Formatting:** Avoids conflicts between prompt placeholders and JSON examples
7. **Modular CLI Design:** Subcommand pattern (agreement/stance) with domain flags
8. **Logging:** Automatic timestamped logs organized by user and date

## Model & Prompt Selection Guide

**Recommended Approach: Use GPT-5-mini as default (GPT-5 series, August 2025)**

Based on comprehensive evaluation results (`src/Traction/evaluation_results.md`):

**Agreement Classification (Monetary):**
- **GPT-5** + Few Shot: **74.74%** accuracy (best overall, F1: 0.7327)
- **GPT-5-mini** + Few Shot: **71.97%** accuracy (recommended cost-effective, F1: 0.6944)
- **GPT-5-nano** + Few Shot: **66.44%** accuracy (budget option, F1: 0.6395)
- Performance gap: ~3% between GPT-5 and GPT-5-mini

**Stance Classification (Monetary):**
- **GPT-5** + Few Shot: **74.05%** average accuracy (78.55% current, 69.55% future)
- **GPT-5-mini** + Few Shot: **65.40%** average accuracy (67.47% current, 63.32% future)
- **Fine-tuned GPT-4.1-mini**: **78-83%** accuracy (see Fine-Tuning section below)
- Performance gap: ~8.6% between GPT-5 and GPT-5-mini (larger than agreement task)

**Model IDs (August 2025 release):**
- `gpt-5-mini-2025-08-07` - Recommended default for most tasks
- `gpt-5-2025-08-07` - Most advanced model, best for complex reasoning
- `gpt-5-nano-2025-08-07` - Most cost-effective option

**Key Findings:**
- **Default recommendation**: Use `gpt-5-mini` with `few_shot` prompts for cost-effective performance
- **Always use Few Shot prompts** - consistently best across ALL models and tasks (2-8% better than other variants)
- **Upgrade to GPT-5 for stance tasks** - larger performance gain (8.6%) vs agreement tasks (3%)
- **Avoid "With Definitions" prompts** - consistently worst performer (3-8% accuracy drop)
- **Fine-tuning delivers significant gains**: Fine-tuned GPT-4.1-mini achieves 78-83% stance accuracy (vs 65% base GPT-5-mini)
- **Temporal difficulty**: Current stance prediction is 4-9% easier than future stance across all models
- **For production stance classification**: Fine-tuning recommended (see `src/Traction/train_eval/`)

## Fine-Tuning Pipeline

**Location**: `src/Traction/train_eval/`

A modular pipeline for fine-tuning GPT-5-mini on monetary/fiscal stance classification using supervised fine-tuning (SFT).

### Quick Start

```bash
cd src/Traction/train_eval
conda activate traction

# Run full pipeline (prepare → finetune → evaluate)
python run_pipeline.py
```

### Pipeline Modules

1. **`training_config.py`**: Configuration (paths, hyperparameters, model settings)
2. **`training_utils.py`**: Shared utilities (logging, API client, file I/O)
3. **`prepare_data.py`**: Convert Excel → OpenAI JSONL format
4. **`finetune.py`**: Upload data & manage fine-tuning jobs
5. **`evaluate.py`**: Calculate metrics & generate reports
6. **`run_pipeline.py`**: End-to-end orchestrator

### Key Features

- **Dual examples**: Generates 2 examples per row (staff + authority texts) → ~2x training data
- **All labels included**: "unclear" and "irrelevant" are valid targets (not filtered)
- **Structured output**: JSON responses validated against Pydantic schemas
- **Comprehensive metrics**: Accuracy, F1, confusion matrices, per-label performance
- **Modular design**: Each script runs independently or as part of pipeline
- **Checkpoint support**: Resume from any step

### Expected Performance

- **Baseline (GPT-5-mini + few_shot)**: 65.40% stance accuracy (monetary)
- **Fine-tuned GPT-4.1-mini achieved**:
  - **Current stance**: 82.76% accuracy (combined), 78.45% (standard)
  - **Future stance**: 77.59% accuracy (combined), 73.28% (standard)
  - **Performance gain**: +13-17% absolute improvement over baseline
- **Training time**: 10-40 minutes
- **Cost**: ~$0.50-2.00 per fine-tuning run (pricing subject to change)

### Usage Examples

```bash
# Step-by-step execution
python prepare_data.py          # Generate train.jsonl, test.jsonl
python finetune.py              # Fine-tune model (10-40 min)
python evaluate.py              # Generate evaluation_report.md

# Custom hyperparameters
python finetune.py --n-epochs 5 --learning-rate-multiplier 1.5

# Resume from checkpoint
python run_pipeline.py --skip-prepare --skip-finetune --model-id ft:gpt-5-mini:xxx
```

### Output Files

After running the pipeline:
- `train.jsonl`, `test.jsonl`: Training/test data in OpenAI format
- `finetuning_metadata.json`: Model ID and job details
- `evaluation_report.md`: Comprehensive metrics report
- `predictions.csv`: All predictions with ground truth
- `metrics.json`: Raw metrics in JSON format

See `src/Traction/train_eval/README.md` for complete documentation.

### Quick Evaluation Summary

For a quick comparison of GPT-4o models with different prompt strategies, see:
- `src/Traction/temp/temp_eval.md` - Clean formatted tables showing Agreement and Stance evaluation results
  - **Agreement**: GPT-4o Chain of Thought performs best (Accuracy: 0.70, F1: 0.6520)
  - **Stance (Raw)**: GPT-4o Chain of Thought performs best (Accuracy: 0.6567, F1: 0.6565)
  - **Stance (Merging Unclear/Irrelevant)**: GPT-4o Simple performs best (Accuracy: 0.7783, F1: 0.7610)

## Quick Reference: Common Workflows

### Full Pipeline (XML → Visualization)

```bash
# 1. Extract paragraphs from XML
python src/Traction/data_preprocess.py

# 2. Classify topics (optional - choose one)
python src/Traction/topic_identification.py --test-mode  # async, small batches
python src/Traction/topic_identification_batch.py        # batch API, large datasets

# 3. Aggregate to document level
python src/Traction/paragraph_back2_doc.py

# 4. Run stance/agreement inference
python src/Traction/inference_agreement_stance.py agreement \
  --domain monetary --submit --post-process

python src/Traction/inference_agreement_stance.py stance \
  --domain fiscal --submit --post-process

# 5. Analyze results (interactive)
jupyter notebook src/Traction/post_estimate_analysis/data_vis.ipynb
```

### Common Inference Patterns

```bash
# Test with sample data before full run
python src/Traction/inference_agreement_stance.py agreement \
  --domain monetary --test-mode --submit --post-process

# Generate JSONL only (for review before submission)
python src/Traction/inference_agreement_stance.py stance \
  --domain fiscal --jsonl-file my_custom_batch.jsonl

# Submit existing JSONL and post-process results
python src/Traction/inference_agreement_stance.py stance \
  --domain fiscal --submit --post-process \
  --results-jsonl /path/to/batch_results_xxx.jsonl

# Use fine-tuned model
python src/Traction/inference_agreement_stance.py stance \
  --domain monetary --model ft:gpt-5-mini:xxx \
  --submit --post-process

# Custom prompt variant
python src/Traction/inference_agreement_stance.py agreement \
  --domain fiscal --prompt-variant chain_of_thought \
  --submit --post-process
```

### Evaluation & Fine-Tuning

```bash
# Evaluate prompts and models
jupyter notebook notebooks/Traction/evaluate_fiscal_monetray_pipeline.ipynb

# Run fine-tuning pipeline
cd src/Traction/train_eval
python run_pipeline.py

# Step-by-step fine-tuning
python prepare_data.py
python finetune.py
python evaluate.py

# Resume from existing fine-tuned model
python evaluate.py --model-id ft:gpt-5-mini:xxx
```

### Visualization Workflows

```python
# In Jupyter notebook or Python script
import pandas as pd
from src.Traction.post_estimate_analysis.data_vis_utils import *

# Load results
df = pd.read_csv('/path/to/agreement_monetary_results.csv')

# Add income groups
df['income_group'] = df['country'].apply(classify_income_group_from_country_name)

# Filter to analysis period
df = filter_year_range(df, start_year=2015, end_year=2023)

# Agreement analysis
df = add_no_disagreement_flag(df)
proportions = compute_no_disagreement_proportions_by_year(
    df, groups=['ALL', 'AE', 'EM', 'LIC']
)
plot_group_lines_by_year(proportions, groups=['ALL', 'AE', 'EM', 'LIC'])

# Stance analysis (requires stance results)
df_stance = pd.read_csv('/path/to/stance_monetary_results.csv')
wide = pivot_stance_wide(df_stance)
share = compute_imf_vs_authority_share(wide, imf_col='imf_staff_stance_current',
                                        auth_col='country_authority_stance_current')
plot_stacked_proportions_by_year(share)
```

## Troubleshooting

### Common Issues

**ImportError: No module named 'libs'**
- Ensure you're running scripts from the repository root
- Scripts add `../../` to sys.path automatically, but this assumes correct directory structure

**OPENAI_API_KEY not set**
- Create `.env` file in repository root with `OPENAI_API_KEY=sk-...`
- The `.env` file is loaded automatically via `python-dotenv`

**Batch API job fails**
- Check batch status: `client.batches.retrieve(batch_id)`
- Download error details from output file
- Common causes: invalid JSONL format, exceeded token limits, schema validation errors

**Stance results show mostly "unclear"**
- Text may not contain stance-relevant content (expected behavior)
- Try `few_shot` or `chain_of_thought` prompts for better disambiguation
- Consider fine-tuning for domain-specific classification

**Agreement pivoting fails**
- Ensure data has both "staff" and "buff" (or "authority") in `type` column
- Check that `id_cols` uniquely identify each document-topic pair
- Verify `text` column is not null
