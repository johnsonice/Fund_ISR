# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

**Completed:**
- [x] Experiment fine-tuned pipeline with the formalized prompts for both monetary and fiscal domains
- [x] Comprehensive evaluation across GPT-4o, GPT-5, GPT-5-mini, and GPT-4.1 fine-tuned models
- [x] Modular fine-tuning pipeline supporting all four task types (monetary/fiscal stance/agreement)
- [x] Incremental data update pipeline for extending analysis to new Article IV reports
- [x] Production inference scripts with fine-tuned GPT-4.1 models (simple prompts as default)

**To Do:**
- [ ] Explore training strategies beyond SFT (e.g., RFT, RLHF)

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
- `data_vis_utils.py`: Reusable visualization utilities (sector-agnostic design, no country classification logic)
- `final_dataset_utils.py`: Authoritative data transformation library — builds `df_fin.csv` / `df_fin_reg_core.csv` from raw inference outputs. Called by `src/Traction/create_final_dataset.py` (main pipeline) and `src/Traction/incremental_update/07b_create_final_dataset_incremental.py` (incremental pipeline)
- `classify_disagreement_areas.py`: LLM-based categorizer for free-text disagreement areas (uses `disagreement_area_cache.json` for caching)
- `data_vis_v4.ipynb`: Latest comprehensive analysis notebook

**Income group classification:**
- Country metadata is maintained in `src/Traction/docs/reference/country_meta_info.xlsx`
- Income groups are assigned via DataFrame merge on ISO3 codes (not hardcoded functions)
- Pattern: `df = df.merge(country_map, left_on='Primary Country Code', right_on='ISO3', how='left')`

**Key capabilities:**
1. **Agreement analysis**:
   - Compute "no disagreement" proportions by year and income group
   - Trend analysis of disagreement areas (e.g., inflation targets, interest rate timing)
   - Category extraction from disagreement text fields
2. **Stance analysis**:
   - Pivot stance data to wide format (IMF vs authority comparison)
   - Compute stance direction scores (loosening/tightening scale)
   - Stacked proportion charts showing IMF advice vs authority policy direction
3. **Data transformation** (`create_final_dataset.py` + `final_dataset_utils.py`):
   - Combines `df_aiv.csv` + 4 per-sector inference results + zero-shot general agreement into document-level analysis datasets
   - Pivots long-format stance data to wide format (staff vs authority side-by-side)
   - Derives combined agreement measures (`mon_agreement_general`, `fis_agreement_general`) from multiple sources
   - Creates 9-category policy mix (monetary x fiscal combinations: MtFt, MnFt, etc.)
   - Cleans hallucinated LLM values and consolidates unclear/no-change stance values
   - Outputs: `df_fin.csv` (full dataset with text columns) and `df_fin_reg_core.csv` (core subset for downstream merging)
4. **Report counting**: Track Article IV report volumes by year and income group

**Example usage (in notebook):**
```python
import pandas as pd
from data_vis_utils import (
    filter_year_range,
    add_no_disagreement_flag,
    compute_no_disagreement_proportions_by_year,
    plot_group_lines_by_year,
    pivot_stance_wide,
    compute_imf_vs_authority_share,
    plot_stacked_proportions_by_year
)

# Load results and country metadata
df = pd.read_csv('agreement_monetary_results.csv')
country_map = pd.read_excel('src/Traction/docs/reference/country_meta_info.xlsx')
df = df.merge(country_map[['ISO3', 'income_group']], left_on='Primary Country Code', right_on='ISO3', how='left')

# Compute and plot agreement trends
df = add_no_disagreement_flag(df, agreement_col='agreement')
proportions = compute_no_disagreement_proportions_by_year(df, groups=['ALL', 'AE', 'EM', 'LIC'])
plot_group_lines_by_year(proportions, groups=['ALL', 'AE', 'EM', 'LIC'])
```

### Incremental Data Update Pipeline

**Location**: `src/Traction/incremental_update/`

An 8-step pipeline for processing new Article IV reports and merging them into the existing dataset:

```bash
# Step 1: Extract metadata from new XML packages
python src/Traction/incremental_update/01_data_preprocess_incremental.py \
  --input-root /path/to/new_xml_packages --output-path /path/to/raw_metadata.xlsx

# Step 2: Postprocess metadata (enrich with country codes, year, AIV flag)
python src/Traction/incremental_update/02_meta_data_postprocess.py \
  --input-path /path/to/raw_metadata.xlsx --output-path /path/to/postprocessed.xlsx

# ⚠ MANDATORY QA GATE: Verify country matching before proceeding
# - Check Country Name extraction from titles
# - Verify Primary Country Code ISO3 matches
# - Create clean metadata workbook with corrections

# Step 3: Extract texts and paragraphs from XML
python src/Traction/incremental_update/03_incremental_aiv_update.py \
  --raw-xml-root /path/to/xml --metadata-path /path/to/clean_metadata.xlsx \
  --output-dir /path/to/incremental_output

# Step 4: Classify topics (Batch API)
bash src/Traction/incremental_update/04_topic_identification_incremental.sh

# Step 5: Aggregate paragraphs to document level
bash src/Traction/incremental_update/05_paragraph_back2_doc_incremental.sh

# Step 6: Run all 4 stance/agreement inference jobs (uses fine-tuned models)
bash src/Traction/incremental_update/06_inference_incremental.sh

# Step 7: Zero-shot general (cross-sector) agreement classification
bash src/Traction/incremental_update/07_general_sentiment_incremental.sh

# Step 7b: Build incremental final dataset (df_fin.csv / df_fin_reg_core.csv)
python src/Traction/incremental_update/07b_create_final_dataset_incremental.py

# Step 8: Merge incremental results with main dataset
python src/Traction/incremental_update/08_merge_all_incremental.py \
  --incremental-dir /path/to/incremental --main-dir /path/to/main

# (Optional) Post-merge analysis on the combined sample
jupyter notebook src/Traction/incremental_update/09_analysis_full_sample.ipynb
```

**Key features:**
- Mandatory QA gate after Step 2 for country matching verification
- Uses fine-tuned GPT-4.1 models with `simple` prompt variant for inference
- Deduplicates by Print ISBN when merging with main dataset
- Original main files are never modified; merged outputs written to incremental directory
- Supports multi-year processing (run Step 3 per year, combine, then continue)
- Detailed workflow documentation: `src/Traction/incremental_update/incremental_update_step.md`

### Inference Shell Scripts

**Location**: `src/Traction/scripts/inference/`

Modular shell scripts for running inference tasks:

```
scripts/inference/
├── run_all.sh                       # Runs all 4 fine-tuned tasks in parallel
├── run_monetary_agreement.sh        # Monetary agreement only
├── run_fiscal_agreement.sh          # Fiscal agreement only
├── run_monetary_stance.sh           # Monetary stance only
├── run_fiscal_stance.sh             # Fiscal stance only
├── run_general_agreement.sh         # Zero-shot cross-sector general agreement
├── run_create_final_dataset.sh      # Build df_fin.csv / df_fin_reg_core.csv
└── run_main_base_refresh.sh         # Orchestrator: parallel inference + final dataset
```

- Default prompt variant: `simple` (optimized for fine-tuned models)
- Override via environment variable: `PROMPT_VARIANT=few_shot bash run_all.sh`
- Uses fine-tuned GPT-4.1 model IDs configured per task
- `run_main_base_refresh.sh` is the recommended entry point for a fresh main-base build: runs `run_all.sh` and `run_general_agreement.sh` in parallel, then builds the final dataset

**Training scripts**: `src/Traction/scripts/training/`
- `prepare_all_tasks.sh`, `finetune_all_tasks.sh`, `evaluate_all_tasks.sh`, `evaluate_single.sh`

### Evaluation & Development

- **Evaluation Pipeline**: `src/Traction/train_eval/evaluate_fiscal_monetray_pipeline.py`
  - Function: `evaluate_prompt_and_model(prompt_key, model_name, data_file, use_full_dataset=True)`
  - Function: `run_comprehensive_evaluation(domains, models, variants)` for batch evaluation
  - Supports monetary/fiscal stance and agreement tasks
  - Auto-sets temperature based on model type (GPT-4o: 0, GPT-5: 1.0)
  - **Latest results**: `src/Traction/docs/evaluation_results_comprehensive_current.md` - GPT-4o vs GPT-5 vs GPT-4.1 fine-tuned comparison
  - Replication results in `src/Traction/docs/evaluation_results_replication.md`
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
    - `inference_agreement_stance.py`: Unified script for per-sector agreement detection and stance classification (monetary/fiscal)
    - `inference_general_agreement.py`: Zero-shot cross-sector general agreement classification (reuses the same Batch API plumbing)
    - Uses OpenAI Batch API for cost efficiency
  - **Final dataset assembly:**
    - `create_final_dataset.py`: Combines `df_aiv.csv` + 4 per-sector inference results + general agreement → `df_fin.csv` and `df_fin_reg_core.csv`
    - Delegates logic to `post_estimate_analysis/final_dataset_utils.py`; shared with the incremental pipeline's `07b_*.py`
  - **Shared utilities:**
    - `llm_batch_process_utils.py`: Message builders and batch processing helpers
    - `config.py`: Cross-platform path configuration
  - **Prompts & schemas:**
    - `prompts/schema.py`: Pydantic models and PROMPT_REGISTRY
    - `prompts/prompt_examples.py`: Task-specific examples, explanations, and column mappings
    - `prompts/*.md`: Markdown prompt templates (4 variants per task)
  - **Post-estimation analysis:**
    - `post_estimate_analysis/data_vis_utils.py`: Visualization utilities (sector-agnostic, no country classification logic)
    - `post_estimate_analysis/final_dataset_utils.py`: Authoritative data transformation library (raw inference → `df_fin.csv` / `df_fin_reg_core.csv`); shared by main and incremental pipelines
    - `post_estimate_analysis/classify_disagreement_areas.py`: LLM-based categorizer for free-text disagreement areas (writes `disagreement_area_cache.json`)
    - `post_estimate_analysis/data_vis_v4.ipynb`: Latest analysis notebook
    - `post_estimate_analysis/adhoc/`: Ad-hoc analysis scripts and one-off notebooks
    - `post_estimate_analysis/ v1/`: Archived legacy notebooks (note the leading space in the directory name) — contains `data_vis.ipynb`, `data_vis_v3.ipynb`, `compare_old_new_pipeline.ipynb`, and `vis_report.md`
  - **Incremental update pipeline:**
    - `incremental_update/01_data_preprocess_incremental.py`: Extract metadata from new XML packages
    - `incremental_update/02_meta_data_postprocess.py`: Enrich metadata with country codes and AIV flag
    - `incremental_update/03_incremental_aiv_update.py`: Extract texts and paragraphs from XML
    - `incremental_update/04_topic_identification_incremental.sh`: Topic classification (Batch API)
    - `incremental_update/05_paragraph_back2_doc_incremental.sh`: Aggregate to document level
    - `incremental_update/06_inference_incremental.sh`: Run 4 stance/agreement inference jobs
    - `incremental_update/07_general_sentiment_incremental.sh`: Zero-shot general cross-sector agreement classification
    - `incremental_update/07b_create_final_dataset_incremental.py`: Build incremental `df_fin.csv` / `df_fin_reg_core.csv` (calls shared `final_dataset_utils.py`)
    - `incremental_update/08_merge_all_incremental.py`: Merge with main dataset (dedup by Print ISBN)
    - `incremental_update/09_analysis_full_sample.ipynb`: Post-merge analysis notebook on the combined sample
    - `incremental_update/incremental_update_step.md`: Detailed workflow documentation
    - `incremental_update/adhoc/`: Ad-hoc scripts for one-off incremental fixes
  - **Shell scripts:**
    - `scripts/inference/`: Modular inference scripts (run_all.sh, per-task scripts)
    - `scripts/training/`: Fine-tuning scripts (prepare, finetune, evaluate)
    - `scripts/run_post_process_all.sh`: Batch post-processing
  - **Fine-tuning & evaluation pipeline:**
    - `train_eval/`: Fine-tuning pipeline for GPT-4.1-mini (see Fine-Tuning section)
    - `train_eval/evaluate_fiscal_monetray_pipeline.py`: Comprehensive model/prompt evaluation
    - `train_eval/README.md`, `train_eval/PIPELINE_DESIGN.md`: Pipeline documentation
  - **Documentation & reference:**
    - `docs/evaluation_results_comprehensive_current.md`: Latest evaluation results (GPT-4o vs GPT-5 vs GPT-4.1 fine-tuned)
    - `docs/evaluation_results_replication.md`: Replication study
    - `docs/evaluation_results_comparison.md`: Side-by-side prompt/model comparison
    - `docs/evaluation_metrics_gpt_5.md`: GPT-5-specific metric breakdowns
    - `docs/Data_Process_Documentation.md`: Data processing documentation
    - `docs/reference/country_meta_info.xlsx`: Country ISO3 codes and income group reference
    - `docs/reference/archieve/`: Archived reference data
  - **Legacy & reference code:**
    - `temp/reference_code/`: Legacy scripts from earlier pipeline iterations (1-13 numbered scripts)
    - `temp/`: Temporary scripts and backups

- **`src/Others/`**: Experimental scripts and one-off analyses
  - `async_inference.py`: Async inference with vLLM server
  - `process_ram_tables/`: RAM table extraction and processing scripts
  - `eval_topic_identification.py`: Topic classification evaluation
  - `post_process_inference_data.py`: Data post-processing utilities

- **`notebooks/Traction/`**: Jupyter notebooks for development and testing
  - `llm_fiscal_eval_demo_v2.ipynb`, `llm_monetary_eval_demo_v2.ipynb`: Per-domain evaluation demos (current v2 versions)
  - `llm_fiscal_monetary_inference_demo.ipynb`: Inference examples
  - `llm_topic_identification_demo.ipynb`: Topic classification demos
  - `archieve/`: Older notebook versions

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
  - `few_shot`: Includes labeled examples (recommended for base models)
  - `chain_of_thought`: Adds reasoning step
- **PROMPT_REGISTRY**: Maps prompt keys to files/models
  - Pattern: `{domain}_{task}_{variant}` (e.g., `monetary_stance_few_shot`)
  - All 17 prompt templates registered for easy access

**7. Post-Processing (`src/Traction/paragraph_back2_doc.py`):**
- Aggregates paragraph-level classifications to document-level summaries
- Creates binary dummy variables for topics with confidence > 30%

**8. Post-Estimation Analysis (`src/Traction/post_estimate_analysis/`):**
- **`data_vis_utils.py`**: Production-ready visualization utilities
  - **DataFrame utilities**: `filter_year_range()`, `coerce_year_int()`, `compute_year_group_counts()`
  - **Agreement analysis**: `add_no_disagreement_flag()`, `compute_no_disagreement_proportions_by_year()`, `extract_categories_from_text()`
  - **Stance analysis**: `pivot_stance_wide()`, `compute_imf_vs_authority_share()`
  - **Plotting helpers**: `plot_group_lines_by_year()`, `plot_stacked_proportions_by_year()`, `plot_category_trends()`
  - **Design philosophy**: Sector-agnostic, composable functions that return data (not side effects)
  - **Note**: Income group classification removed from this module; now done via external reference file merge
- **`final_dataset_utils.py`**: Authoritative library that builds `df_fin.csv` / `df_fin_reg_core.csv` from raw inference outputs
  - Pivots long-format stance data to wide (staff vs authority side-by-side)
  - Derives combined agreement measures (`mon_agreement_general`, `fis_agreement_general`)
  - Creates 9-category policy mix (MtFt, MnFt, etc.)
  - Cleans hallucinated LLM values and consolidates unclear/no-change values
  - Invoked by `src/Traction/create_final_dataset.py` (main pipeline) and `src/Traction/incremental_update/07b_create_final_dataset_incremental.py` (incremental pipeline)
- **`classify_disagreement_areas.py`**: Categorizes free-text disagreement areas via LLM; persists results in `disagreement_area_cache.json`
- **Country reference**: `docs/reference/country_meta_info.xlsx` — ISO3 codes and income group mappings
- **Notebooks:**
  - `data_vis_v4.ipynb`: Latest comprehensive analysis notebook (current version)
  - `adhoc/`: One-off analysis scripts and notebooks
  - ` v1/`: Archived legacy notebooks (leading space in directory name) — `data_vis.ipynb`, `data_vis_v3.ipynb`, `compare_old_new_pipeline.ipynb`, `vis_report.md`

**9. Incremental Update Pipeline (`src/Traction/incremental_update/`):**
- Multi-step pipeline for processing new Article IV reports and merging with existing data
- Steps: XML metadata extraction → postprocessing → QA gate → text extraction → topic classification → aggregation → per-domain inference → general zero-shot sentiment → final dataset build → merge → analysis
- Uses fine-tuned GPT-4.1 models with `simple` prompts for inference
- Step 07b (`07b_create_final_dataset_incremental.py`) reuses the shared `final_dataset_utils.py` so incremental and main pipelines produce identically-shaped outputs
- Deduplicates by Print ISBN when merging; original main files never modified
- Post-merge analysis lives in `09_analysis_full_sample.ipynb`
- See Incremental Data Update Pipeline section for full details

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
- Recommended models:
  - **Production**: Fine-tuned `gpt-4.1-mini` (best accuracy)
  - **Zero-shot**: `gpt-5` (premium), `gpt-5-mini` (cost-effective), `gpt-5-nano` (budget)
- Model IDs:
  - `gpt-4.1-mini-2025-04-14` (fine-tuning base, April 2025)
  - `gpt-5-2025-08-07`, `gpt-5-mini-2025-08-07`, `gpt-5-nano-2025-08-07` (August 2025)
  - `gpt-4o-2024-08-06` (legacy comparison)

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
    ├── *.csv                # Main pipeline outputs
    └── incremental_update/  # Incremental update outputs
        └── {run_name}/      # Per-run directory (e.g., 05252026_update)
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

**Final dataset outputs (from `create_final_dataset.py` / `07b_create_final_dataset_incremental.py`):**
- `df_fin.csv`: Full analysis-ready dataset with text columns + `policy_mix_staff` / `policy_mix_buff`
- `df_fin_reg_core.csv`: Core subset matching the archive schema (consumed by `08_merge_all_incremental.py`)
- `df_documents_general.csv`: Zero-shot cross-sector general agreement results (input to final dataset build)

**Post-analysis outputs (from `data_vis_v4.ipynb`):**
- Income group enhanced datasets (via `docs/reference/country_meta_info.xlsx` merge)
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
│ STAGE 5: Final Dataset Assembly + Analysis & Visualization              │
├─────────────────────────────────────────────────────────────────────────┤
│ Input:  agreement/stance results CSVs + general agreement CSV           │
│ Tools:  create_final_dataset.py (+ final_dataset_utils.py)              │
│         post_estimate_analysis/data_vis_utils.py                        │
│         post_estimate_analysis/data_vis_v4.ipynb                        │
│ Output: - df_fin.csv / df_fin_reg_core.csv (analysis-ready datasets)    │
│         - Income group classifications                                  │
│         - Agreement trend charts                                        │
│         - Stance comparison charts (IMF vs authorities)                 │
│         - Disagreement area analysis                                    │
│         - Publication-ready visualizations                              │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key decision points:**
- **Async vs Batch API**: Use async for <5K rows, batch API for larger datasets
- **Prompt variant**: Use `simple` for fine-tuned models (default), `few_shot` for base models
- **Model selection**: Fine-tuned GPT-4.1 (production default), `gpt-5` (premium zero-shot), `gpt-5-mini` (cost-effective zero-shot)

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

**Recommended Approach: Use GPT-4.1 fine-tuned for production, GPT-5 for zero-shot**

Based on comprehensive evaluation results (`src/Traction/docs/evaluation_results_comprehensive_current.md`):

**Production Recommendation: Fine-tuned GPT-4.1-mini**
- Consistently outperforms all base models across all tasks
- 10-18% absolute improvement over base GPT-5-mini
- Simple prompts work best with fine-tuned models

**Zero-shot Model Selection:**

| Use Case | Model | Prompt | Expected Accuracy |
|----------|-------|--------|-------------------|
| Agreement (cost-effective) | GPT-5-mini | Few-shot | ~71-72% |
| Agreement (best quality) | GPT-5 | Few-shot | ~74% |
| Stance (cost-effective) | GPT-5-mini | Few-shot | ~67-68% |
| Stance (best quality) | GPT-5 | Few-shot | ~75-79% |
| Production (all tasks) | GPT-4.1 Fine-tuned | Simple | ~74-84% |

**Model IDs:**
- `gpt-4.1-mini-2025-04-14` - Base model for fine-tuning (April 2025)
- `gpt-5-mini-2025-08-07` - Cost-effective zero-shot (August 2025)
- `gpt-5-2025-08-07` - Best zero-shot performance (August 2025)
- `gpt-4o-2024-08-06` - Legacy comparison baseline

**Fine-tuned Model IDs (production):**
- Monetary Agreement: `ft:gpt-4.1-2025-04-14:protagolabs:monetary-agreement:D2McIjCy`
- Fiscal Agreement: `ft:gpt-4.1-2025-04-14:protagolabs:fiscal-agreement:D2O1nc5q`
- Monetary Stance: `ft:gpt-4.1-2025-04-14:protagolabs:monetary-stance:D2K6qCDj`
- Fiscal Stance: `ft:gpt-4.1-2025-04-14:protagolabs:fiscal-stance:D2Lw2NJZ`

**Key Findings:**
- **Fine-tuning is recommended** for production use - delivers 10-18% gains
- **Use `simple` prompts** with fine-tuned models (default in all inference scripts)
- **Use `few_shot` prompts** with base models - 2-8% better than other variants
- **GPT-5 series outperforms GPT-4o** by 5-15% on stance tasks
- **Avoid "With Definitions" prompts** - consistently worst performer
- **Current stance is easier** than future stance by 4-9% across all models
- **Merging unclear/irrelevant** improves stance metrics by 5-10%

## Fine-Tuning Pipeline

**Location**: `src/Traction/train_eval/`

A modular pipeline for fine-tuning GPT-4.1-mini on monetary/fiscal stance and agreement classification using supervised fine-tuning (SFT).

### Quick Start

```bash
cd src/Traction/train_eval
conda activate traction

# Run full pipeline (prepare → finetune → evaluate)
python run_pipeline.py
```

### Pipeline Modules

1. **`training_config.py`**: Configuration (paths, hyperparameters, model settings)
   - Supports all four task types: `monetary_stance`, `fiscal_stance`, `monetary_agreement`, `fiscal_agreement`
   - Base model: `gpt-4.1-mini-2025-04-14` (GPT-4.1 series, April 2025)
   - Task-specific Excel column mappings and label definitions
2. **`training_utils.py`**: Shared utilities (logging, API client, file I/O)
3. **`prepare_data.py`**: Convert Excel → OpenAI JSONL format
4. **`finetune.py`**: Upload data & manage fine-tuning jobs
5. **`evaluate.py`**: Calculate metrics & generate reports
6. **`evaluate_fiscal_monetray_pipeline.py`**: Comprehensive evaluation script for comparing prompts and models
7. **`run_pipeline.py`**: End-to-end orchestrator

### Key Features

- **Multi-task support**: All four task types (monetary/fiscal × stance/agreement)
- **Dual examples**: Generates 2 examples per row (staff + authority texts) → ~2x training data
- **All labels included**: "unclear" and "irrelevant" are valid targets (not filtered)
- **Structured output**: JSON responses validated against Pydantic schemas
- **Comprehensive metrics**: Accuracy, F1, confusion matrices, per-label performance
- **Modular design**: Each script runs independently or as part of pipeline
- **Checkpoint support**: Resume from any step

### Expected Performance

Based on comprehensive evaluation (`src/Traction/docs/evaluation_results_comprehensive_current.md`):

**GPT-4.1 Fine-tuned Performance:**
| Task | Metric | Value |
|------|--------|-------|
| Monetary Agreement | Accuracy | **77.59%** |
| Monetary Stance (Current) | Accuracy | **83.62%** |
| Monetary Stance (Future) | Accuracy | **74.14%** |
| Fiscal Agreement | Accuracy | **80.00%** |
| Fiscal Stance | Accuracy | **74.17%** |

**Performance gain over baseline GPT-5-mini**: +10-18% absolute improvement

### Usage Examples

```bash
# Step-by-step execution
python prepare_data.py          # Generate train.jsonl, test.jsonl
python finetune.py              # Fine-tune model
python evaluate.py              # Generate evaluation_report.md

# Comprehensive evaluation across models and prompts
python evaluate_fiscal_monetray_pipeline.py

# In Python:
from evaluate_fiscal_monetray_pipeline import run_comprehensive_evaluation
df = run_comprehensive_evaluation(
    domains=['monetary', 'fiscal'],
    models=['gpt-4o-2024-08-06', 'gpt-5-2025-08-07'],
    variants=['simple', 'few_shot', 'chain_of_thought']
)
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

**Latest Comprehensive Results** (`src/Traction/docs/evaluation_results_comprehensive_current.md`):

**Best Model Performance by Task:**

| Task | Best Model | Accuracy | Notes |
|------|-----------|----------|-------|
| Monetary Agreement | GPT-4.1 Fine-tuned | **77.59%** | Simple prompt |
| Monetary Stance (Current) | GPT-4.1 Fine-tuned | **83.62%** | Simple prompt |
| Monetary Stance (Future) | GPT-4.1 Fine-tuned | **74.14%** | Simple prompt |
| Fiscal Agreement | GPT-4.1 Fine-tuned | **80.00%** | Simple prompt |
| Fiscal Stance | GPT-4.1 Fine-tuned | **74.17%** | Simple prompt |

**Model Comparison (best results per model):**

| Model | Monetary Agreement | Monetary Stance | Fiscal Agreement | Fiscal Stance |
|-------|-------------------|-----------------|------------------|---------------|
| GPT-4.1 Fine-tuned | 77.59% | 83.62%/74.14% | 80.00% | 74.17% |
| GPT-5 | 74.05% (Few-shot) | 79.41%/69.55% | 72.33% | 69.50% |
| GPT-5-mini | 71.63% | 67.47%/67.82% | 70.00% | 68.17% |
| GPT-4o | 73.70% | 64.19%/66.78% | 70.00% | 65.67% |

**Key Insights:**
- **Fine-tuning delivers significant gains**: GPT-4.1 fine-tuned consistently outperforms all base models
- **GPT-5 > GPT-5-mini > GPT-4o** for base model performance
- **Few-shot prompts** work best for GPT-5 series
- **Merging unclear/irrelevant labels** improves stance accuracy by 5-10%
- Current stance prediction is 4-9% easier than future stance across all models

**Documentation locations:**
- `src/Traction/docs/evaluation_results_comprehensive_current.md` - Full comparison table
- `src/Traction/docs/evaluation_results_replication.md` - Replication study details
- `src/Traction/docs/evaluation_metrics_gpt_5.md` - GPT-5 specific metrics

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

# 4. Run stance/agreement inference (per-sector + general)
bash src/Traction/scripts/inference/run_all.sh                    # 4 fine-tuned tasks in parallel
bash src/Traction/scripts/inference/run_general_agreement.sh      # zero-shot cross-sector
# Or, for a fresh main-base build, run both groups + final dataset in one shot:
bash src/Traction/scripts/inference/run_main_base_refresh.sh

# 5. Transform results into final dataset
python src/Traction/create_final_dataset.py
# (or via the shell wrapper: bash src/Traction/scripts/inference/run_create_final_dataset.sh)

# 6. Analyze and visualize results
jupyter notebook src/Traction/post_estimate_analysis/data_vis_v4.ipynb
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
# Run comprehensive evaluation across models and prompts
cd src/Traction/train_eval
python evaluate_fiscal_monetray_pipeline.py

# In Python - run batch evaluation
from evaluate_fiscal_monetray_pipeline import run_comprehensive_evaluation
df = run_comprehensive_evaluation(
    domains=['monetary', 'fiscal'],
    models=['gpt-4o-2024-08-06', 'gpt-5-2025-08-07'],
    variants=['simple', 'few_shot', 'chain_of_thought'],
    save_results=True
)

# Run fine-tuning pipeline
python run_pipeline.py

# Step-by-step fine-tuning
python prepare_data.py
python finetune.py
python evaluate.py

# Resume from existing fine-tuned model
python evaluate.py --model-id ft:gpt-4.1-mini:xxx
```

### Visualization Workflows

```python
# In Jupyter notebook or Python script
import pandas as pd
from src.Traction.post_estimate_analysis.data_vis_utils import *

# Load results and country metadata
df = pd.read_csv('/path/to/agreement_monetary_results.csv')
country_map = pd.read_excel('src/Traction/docs/reference/country_meta_info.xlsx')
df = df.merge(country_map[['ISO3', 'income_group']], left_on='Primary Country Code', right_on='ISO3', how='left')

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

**Recommended entry points for analysis:**
- `src/Traction/create_final_dataset.py`: Authoritative data transformation (raw inference → `df_fin.csv` / `df_fin_reg_core.csv`)
- `src/Traction/post_estimate_analysis/data_vis_v4.ipynb`: Latest comprehensive analysis
- `src/Traction/post_estimate_analysis/ v1/compare_old_new_pipeline.ipynb`: Compare pipeline versions (in archived ` v1/` dir)

### Incremental Update Workflow

```bash
cd src/Traction/incremental_update

# Full incremental pipeline (after QA gate at step 2)
python 01_data_preprocess_incremental.py --input-root /path/to/new_xml
python 02_meta_data_postprocess.py --input-path /path/to/raw_metadata.xlsx

# ⚠ Manual QA: verify country matching, create clean metadata workbook

python 03_incremental_aiv_update.py --raw-xml-root /path/to/xml \
  --metadata-path /path/to/clean_metadata.xlsx --output-dir /path/to/output
bash 04_topic_identification_incremental.sh
bash 05_paragraph_back2_doc_incremental.sh
bash 06_inference_incremental.sh
bash 07_general_sentiment_incremental.sh
python 08_merge_all_incremental.py --incremental-dir /path/to/incremental \
  --main-dir /path/to/main
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
