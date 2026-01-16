# AI Tools for 2025 Interim Surveillance Review

## Overview
Complete end-to-end AI pipeline for analyzing IMF Article IV consultation reports. Automatically extracts macroeconomic topics, classifies policy stances (monetary/fiscal), detects staff-authorities agreement/disagreement, and generates publication-ready visualizations using OpenAI language models.

**Pipeline Coverage:** XML extraction → Topic classification → Stance/agreement inference → Statistical analysis → Visualization

**Latest Updates (January 2026):**
- ✨ Batch execution scripts for parallel inference processing
- ✨ Comprehensive prompt library with 17+ templates (4 variants per task)
- ✨ Complete evaluation study with GPT-4o/GPT-4o-mini/GPT-3.5-turbo
- ✨ Flexible message building system with multi-column template support
- ✨ PROMPT_REGISTRY for automatic schema-prompt mapping

## Key Features
- **Topic Classification**: Classify paragraphs into 6 predefined macroeconomic categories with confidence scores (0-100)
- **Stance Detection**: Extract monetary/fiscal policy stance (current + future direction) for both IMF staff and country authorities
- **Agreement Analysis**: Identify staff-authorities agreement/disagreement with specific disagreement area extraction
- **Production-Ready Inference**: Unified CLI (`inference_agreement_stance.py`) for both monetary and fiscal domains
- **Batch Execution Scripts**: Shell scripts for parallel processing of all inference tasks with test/production modes
- **Batch Processing**: Cost-effective large-scale analysis using OpenAI Batch API (50% cost reduction)
- **Post-Estimation Analysis**: Income group classification, trend analysis, and publication-quality charts
- **Comprehensive Prompt Library**: 17+ prompts with 4 variants per task (simple, with_definitions, few_shot, chain_of_thought)
- **Structured Output**: Pydantic-validated responses with paragraph and document-level aggregations
- **Fine-Tuning Support**: Complete pipeline for fine-tuning GPT-5-mini on domain-specific stance classification
- **Flexible Message Building**: Template-based system supporting multi-column inputs with safe placeholder formatting

## Environment Setup

**Conda Environment:**
```bash
conda activate traction
pip install -r requirements.txt
```

**API Configuration:**
Create `.env` file at project root:
```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

**Data Directory:**
External data should be placed at `~/dev/Fund/CSR/Tractions/` (Linux) or configured OneDrive path (Windows). See `src/Traction/config.py` for details.

## Project Structure

- **`libs/`** - Reusable utilities (LLM wrappers, prompt loaders, batch processing, text utilities)
- **`src/Traction/`** - Main pipeline modules:
  - `data_preprocess.py` - XML paragraph extraction
  - `topic_identification*.py` - Topic classification (async/batch)
  - `paragraph_back2_doc.py` - Document-level aggregation
  - **`inference_agreement_stance.py`** - **Production stance/agreement inference** (NEW)
  - `llm_batch_process_utils.py` - Flexible message building utilities (NEW)
  - **`scripts/`** - **Batch execution shell scripts** (NEW)
  - `post_estimate_analysis/` - Visualization toolkit (NEW)
  - `train_eval/` - Fine-tuning pipeline for GPT-5-mini
- **`src/Traction/prompts/`** - 17+ Pydantic schemas and markdown prompt templates
  - 4 variants per task: simple, with_definitions, **few_shot** (recommended), chain_of_thought
  - Supports: topic classification, monetary/fiscal stance, monetary/fiscal agreement
  - **PROMPT_REGISTRY** maps prompt keys to files and Pydantic response models
- **`notebooks/Traction/`** - Evaluation notebooks, inference demos, and interactive analysis
- **`src/Others/`** - Experimental scripts (vLLM inference, RAM table processing)

## Pipeline Overview

**Complete 5-Stage Workflow:**

```
Stage 1: XML Extraction
  └─> data_preprocess.py → df_paragraphs.csv

Stage 2: Topic Classification (Optional)
  └─> topic_identification*.py → paragraph_with_sector.csv

Stage 3: Document Aggregation
  └─> paragraph_back2_doc.py → document_by_type_sector.csv

Stage 4: Stance & Agreement Inference (PRODUCTION)
  └─> inference_agreement_stance.py → agreement/stance results CSVs
      ├─ Agreement: monetary/fiscal (disagreement area extraction)
      └─ Stance: monetary/fiscal (current + future direction)

Stage 5: Post-Estimation Analysis
  └─> post_estimate_analysis/data_vis.ipynb → Publication charts
      ├─ Income group trends (AE/EM/LC)
      ├─ Agreement proportions over time
      ├─ IMF vs authorities stance comparison
      └─ Disagreement area categorization
```

**Key Scripts:**
- `data_preprocess.py` - Extract paragraphs from XML (Staff Appraisal, Buff Statement, Staff Report, Authorities' Views)
- `topic_identification.py` / `topic_identification_batch.py` - Topic classification (async or batch)
- `paragraph_back2_doc.py` - Aggregate to document level
- **`inference_agreement_stance.py`** - **Unified stance/agreement inference CLI** (monetary & fiscal)
- **`scripts/run_all.sh`** - **Parallel execution orchestrator** (runs all 4 inference tasks)
- **`scripts/run_{domain}_{task}.sh`** - **Individual task runners** (monetary/fiscal × stance/agreement)
- `post_estimate_analysis/data_vis_utils.py` - Visualization utilities (sector-agnostic, composable)
- `llm_batch_process_utils.py` - Flexible message building with multi-column template support

**Topic Categories:**
1. Economic Outlook (GDP, growth, forecasts)
2. Monetary Policy (interest rates, inflation, central bank)
3. Fiscal Stance (spending, debt, budget)
4. Financial Stability (banking, financial risks)
5. External Stance (balance of payments, exchange rates)
6. Other

## Usage

### Quick Start (Complete Pipeline)

```bash
conda activate traction

# Step 1: Extract paragraphs from XML
python src/Traction/data_preprocess.py

# Step 2: Classify topics (optional - choose one)
python src/Traction/topic_identification.py              # Async (fast for small batches)
python src/Traction/topic_identification_batch.py        # Batch API (cost-effective, large scale)
python src/Traction/topic_identification.py --test-mode  # Test mode (sample data)

# Step 3: Aggregate to document level
python src/Traction/paragraph_back2_doc.py

# Step 4: Run stance & agreement inference (PRODUCTION)

# Option A: Use batch execution scripts (recommended for parallel processing)
bash src/Traction/scripts/run_all.sh                     # Run all tasks in parallel
bash src/Traction/scripts/run_monetary_stance.sh         # Monetary stance only
bash src/Traction/scripts/run_monetary_agreement.sh      # Monetary agreement only
bash src/Traction/scripts/run_fiscal_stance.sh           # Fiscal stance only
bash src/Traction/scripts/run_fiscal_agreement.sh        # Fiscal agreement only

# Option B: Use CLI directly
# Monetary agreement
python src/Traction/inference_agreement_stance.py agreement \
  --domain monetary --submit --post-process

# Fiscal stance
python src/Traction/inference_agreement_stance.py stance \
  --domain fiscal --submit --post-process

# Step 5: Analyze results
jupyter notebook src/Traction/post_estimate_analysis/data_vis.ipynb
```

### Stance & Agreement Inference Options

```bash
# Test mode (sample 1000 rows before full run)
python src/Traction/inference_agreement_stance.py agreement \
  --domain monetary --test-mode --submit --post-process

# Custom model and prompt variant
python src/Traction/inference_agreement_stance.py stance \
  --domain fiscal \
  --model gpt-5-mini \
  --prompt-variant few_shot \
  --submit --post-process

# Generate JSONL only (for review before submission)
python src/Traction/inference_agreement_stance.py stance \
  --domain monetary --jsonl-file my_batch.jsonl

# Use fine-tuned model
python src/Traction/inference_agreement_stance.py stance \
  --domain monetary --model ft:gpt-5-mini:xxx --submit --post-process

# Customize sample size for test mode
python src/Traction/inference_agreement_stance.py stance \
  --domain monetary --test-mode --sample-size 100 --submit --post-process
```

### Batch Execution Scripts

The `scripts/` directory provides convenient shell scripts for running inference tasks in parallel:

```bash
# Run all 4 tasks in parallel (monetary/fiscal × stance/agreement)
bash src/Traction/scripts/run_all.sh

# Individual scripts (run with environment variable to customize prompt)
PROMPT_VARIANT=few_shot bash src/Traction/scripts/run_monetary_stance.sh
PROMPT_VARIANT=chain_of_thought bash src/Traction/scripts/run_fiscal_agreement.sh
```

**Features:**
- Automatic conda environment activation
- Configurable prompt variants via `PROMPT_VARIANT` environment variable (default: `few_shot`)
- Test mode enabled by default with configurable sample sizes
- Parallel execution with failure detection (`run_all.sh`)

**Available Tasks:**
- `agreement` - Detect staff-authorities agreement/disagreement (requires staff + authority texts)
- `stance` - Classify policy stance for individual texts (current + future direction)

**Available Domains:**
- `monetary` - Monetary policy analysis (restrictive/neutral/accommodative)
- `fiscal` - Fiscal policy analysis (contractionary/neutral/expansionary)

### Outputs

**After preprocessing:**
- `output/df_paragraphs.csv` - Paragraph-level text
- `output/df_aiv.csv` - Document-level metadata

**After topic classification:**
- `output/paragraph_with_sector*.csv` - Classified paragraphs with confidence scores
- `output/document_by_type_sector.csv` - Document-level topic summaries

**After stance/agreement inference:**
- `agreement_monetary_results.csv` - Monetary agreement classifications with disagreement areas
- `agreement_fiscal_results.csv` - Fiscal agreement classifications
- `stance_monetary_results.csv` - Monetary stance (current + future) for each text
- `stance_fiscal_results.csv` - Fiscal stance classifications

### Evaluation & Fine-Tuning

**Evaluate prompts and models:**
```bash
jupyter notebook notebooks/Traction/evaluate_fiscal_monetray_pipeline.ipynb
```

**Latest Evaluation Results (January 2026):**

Comprehensive evaluation comparing GPT-4o, GPT-4o-mini, and GPT-3.5-turbo across multiple prompt strategies is available in [evaluation_results_replication.md](src/Traction/evaluation_results_replication.md).

**Key Highlights:**
- **Monetary Agreement**: GPT-4o + Simple Short achieves 73.7% accuracy
- **Monetary Stance**: GPT-4o + Few-shot achieves 70.1% accuracy (merged labels)
- **Fiscal Agreement**: GPT-4o achieves 70.0% accuracy (consistent across prompts)
- **Fiscal Stance**: GPT-4o + Simple achieves 77.8% accuracy (merged labels)

**Fine-tune GPT-4o-mini for stance classification:**
```bash
cd src/Traction/train_eval
python run_pipeline.py  # Complete pipeline (prepare → train → evaluate)

# Or step-by-step
python prepare_data.py
python finetune.py
python evaluate.py
```

Fine-tuning documentation available in [train_eval/README.md](src/Traction/train_eval/README.md).

## Model Selection Guide

**Recommended: GPT-4o (Latest evaluation: January 2026)**

Based on comprehensive evaluation results (`src/Traction/evaluation_results_replication.md`):

### Monetary Policy Tasks

**Agreement Classification:**
- **GPT-4o** + Simple Short: **73.7% accuracy** (BEST, F1: 0.713)
- GPT-4o + Few-shot: 72.3% accuracy (F1: 0.707)
- GPT-4o + Chain of Thought: 72.0% accuracy (F1: 0.707)
- GPT-4o-mini + Simple: 70.6% accuracy (F1: 0.665)
- GPT-3.5-turbo + Simple: 55.4% accuracy (baseline)

**Stance Classification:**
- **GPT-4o** + Few-shot: **64.2% current, 66.1% future** (BEST raw accuracy)
- GPT-4o + Few-shot (merged unclear/irrelevant): **70.1% current, 69.7% future**
- GPT-4o + Simple (merged): 64.4% current, 70.4% future
- GPT-4o-mini + Simple: 56.9% current, 65.4% future
- Fine-tuning potential: Target >75% accuracy (see [train_eval/](src/Traction/train_eval/))

### Fiscal Policy Tasks

**Agreement Classification:**
- **GPT-4o** + Any variant: **70.0% accuracy** (consistent across all prompts)
  - Best F1 score: Chain of Thought (0.652)
- GPT-4o-mini + Simple: 64.7% accuracy (F1: 0.573)
- GPT-3.5-turbo + Simple: 57.7% accuracy (baseline)

**Stance Classification:**
- **GPT-4o** + Simple (merged unclear/irrelevant): **77.8% accuracy** (BEST, F1: 0.761)
- GPT-4o + With Definition (merged): 77.0% accuracy (F1: 0.755)
- GPT-4o + Chain of Thought: 65.7% accuracy (raw), 76.2% (merged)
- GPT-4o-mini + Simple: 55.5% accuracy (raw), 55.8% (merged)

### Model Selection Strategy

| Use Case | Recommended Model + Prompt | Expected Accuracy | Notes |
|----------|---------------------------|-------------------|-------|
| **Monetary Agreement** | GPT-4o + Simple Short | 73.7% | Best overall |
| **Monetary Stance** | GPT-4o + Few-shot | 64-70% | Merge unclear/irrelevant for better results |
| **Fiscal Agreement** | GPT-4o + Chain of Thought | 70.0% | Consistent across all variants |
| **Fiscal Stance** | GPT-4o + Simple | 77.8% | Best with merged labels |
| **Budget-conscious** | GPT-4o-mini + Simple | 56-71% | 60-70% cost reduction |
| **Fine-tuning** | Fine-tuned GPT-4o-mini | Target >75% | See [train_eval/](src/Traction/train_eval/) |

**Available Model IDs (January 2026):**
- `gpt-4o` - Current flagship model (recommended)
- `gpt-4o-mini` - Cost-effective option
- `gpt-3.5-turbo` - Legacy baseline (not recommended)

**Key Findings (January 2026 Evaluation):**
- ✅ **GPT-4o consistently outperforms GPT-4o-mini** across all tasks
- ✅ **Prompt selection matters**: Few-shot best for monetary stance, Simple best for fiscal stance
- ✅ **Merging unclear/irrelevant labels** improves accuracy by 5-13% for stance tasks
- ✅ **Fiscal stance easier than monetary**: 77.8% vs 70.1% accuracy with merged labels
- ⚠️ **No single "best prompt"**: Optimal varies by task (simple vs few_shot vs chain_of_thought)
- ⚠️ **GPT-3.5-turbo significantly underperforms**: 55-59% accuracy (15-20% gap vs GPT-4o)

## Post-Estimation Analysis

The `post_estimate_analysis/` toolkit provides production-ready visualization and statistical analysis:

### Features
- **Income group classification**: Auto-classify countries into AE (advanced economies), EM (emerging markets), LC (low-income)
- **Agreement analysis**:
  - Compute "no disagreement" proportions by year and income group
  - Extract and categorize disagreement areas (e.g., inflation targets, interest rate timing)
  - Multi-year trend visualization
- **Stance analysis**:
  - Pivot stance data to wide format (IMF staff vs country authorities)
  - Compute stance direction scores (loosening/tightening scale)
  - Stacked proportion charts comparing policy positions
- **Report tracking**: Article IV report volumes by year and income group

### Example Usage

```python
import pandas as pd
from src.Traction.post_estimate_analysis.data_vis_utils import *

# Load and prepare data
df = pd.read_csv('agreement_monetary_results.csv')
df['income_group'] = df['country'].apply(classify_income_group_from_country_name)
df = filter_year_range(df, start_year=2015, end_year=2023)

# Agreement trends
df = add_no_disagreement_flag(df)
proportions = compute_no_disagreement_proportions_by_year(df, groups=['ALL', 'AE', 'EM', 'LIC'])
plot_group_lines_by_year(proportions, groups=['ALL', 'AE', 'EM', 'LIC'])

# Stance comparison (IMF vs authorities)
df_stance = pd.read_csv('stance_monetary_results.csv')
wide = pivot_stance_wide(df_stance)
share = compute_imf_vs_authority_share(wide, imf_col='imf_staff_stance_current',
                                        auth_col='country_authority_stance_current')
plot_stacked_proportions_by_year(share)
```

See `src/Traction/post_estimate_analysis/data_vis.ipynb` for complete examples.

## Prompt Library & Message Building

### Comprehensive Prompt Collection

The [prompts/](src/Traction/prompts/) directory contains 17+ production-ready markdown templates with systematic organization:

**Prompt Variants (4 per task):**
1. **`simple`** - Minimal instructions, fastest processing
2. **`with_definitions`** - Detailed category definitions and guidelines
3. **`few_shot`** - Includes example inputs/outputs (often performs best)
4. **`chain_of_thought`** - Adds reasoning step before classification

**Available Prompts:**
- `topic_classification.md` - 6-category macroeconomic topic classifier
- `monetary_stance_{variant}.md` - Monetary policy stance (4 variants)
- `monetary_agreement_{variant}.md` - Staff-authorities monetary agreement (4 variants)
- `fiscal_stance_{variant}.md` - Fiscal policy stance (4 variants)
- `fiscal_agreement_{variant}.md` - Staff-authorities fiscal agreement (4 variants)

**Template Placeholders:**
- `{TEXT}` - Single text input
- `{STAFF}`, `{AUTHORITY}` - Multi-column inputs for agreement tasks
- `{COUNTRY}`, `{YEAR}`, `{TYPE}` - Metadata fields
- `{EXPLANATION}`, `{EXAMPLES}` - Dynamic content injection

### PROMPT_REGISTRY

The [prompts/schema.py](src/Traction/prompts/schema.py) module provides automatic mapping:

```python
from src.Traction.prompts.schema import PROMPT_REGISTRY

# Automatically loads prompt file and Pydantic response model
registry_entry = PROMPT_REGISTRY['monetary_stance_few_shot']
# registry_entry = {
#     'file': 'monetary_stance_few_shot.md',
#     'response_model': MonetaryStanceResponse
# }
```

**Pydantic Response Models:**
- `TopicResponse` - Topic classification with confidence scores
- `MonetaryStanceResponse` / `MonetaryStanceChainOfThoughtResponse` - Current + future stance
- `MonetaryAgreementResponse` / `MonetaryAgreementChainOfThoughtResponse` - Agreement + disagreement areas
- `FiscalStanceResponse` / `FiscalStanceChainOfThoughtResponse` - Fiscal stance classification
- `FiscalAgreementResponse` / `FiscalAgreementChainOfThoughtResponse` - Fiscal agreement detection

### Flexible Message Building

The [llm_batch_process_utils.py](src/Traction/llm_batch_process_utils.py) module provides template-based message building:

**Key Functions:**
- `_build_batch_messages_from_df()` - Single-column simple processing
- `_build_batch_messages_from_df_flexible()` - Multi-column template system
  - Supports placeholders like `{STAFF}`, `{AUTHORITY}`, `{COUNTRY}`, `{YEAR}`
  - Safe placeholder formatting (avoids conflicts with JSON examples in prompts)
  - Flexible column mapping: `column_mapping={'STAFF': 'imf_text', 'AUTHORITY': 'auth_text'}`

**Example Usage:**
```python
from src.Traction.llm_batch_process_utils import _build_batch_messages_from_df_flexible

# Agreement task: merge staff + authority texts
messages = _build_batch_messages_from_df_flexible(
    df=df,
    system_prompt="You are an IMF policy analyst...",
    user_prompt_template="Staff view: {STAFF}\n\nAuthority view: {AUTHORITY}\n\nDo they agree?",
    column_mapping={'STAFF': 'staff_text', 'AUTHORITY': 'authority_text'},
    id_column='document_id'
)
```

## Project Status

**Completed:**
- [x] ~~Replicate Xiaorui's topic tagging workflow with full reproducibility~~
- [x] ~~Implement monetary and fiscal policy stance extraction with agreement metrics~~
- [x] ~~Extend document ingestion to cover 2024-2025 Article IV reports~~
- [x] ~~Develop External Sector methodology for balance/exchange rate analysis~~
- [x] **Build production pipeline for stance and agreement classification ([inference_agreement_stance.py](src/Traction/inference_agreement_stance.py))**
- [x] **Implement flexible batch processing utilities for multi-column prompts ([llm_batch_process_utils.py](src/Traction/llm_batch_process_utils.py))**
- [x] **Create post-estimation analysis toolkit with publication-ready visualizations ([post_estimate_analysis/](src/Traction/post_estimate_analysis/))**
- [x] **Develop fine-tuning pipeline for domain-specific stance classification ([train_eval/](src/Traction/train_eval/))**
- [x] **Build complete pipeline for fiscal policy stance and agreement classification**
- [x] **Reproduce all data visualizations with updated results**
- [x] **Create batch execution scripts for parallel inference ([scripts/](src/Traction/scripts/))** (Jan 2026)
- [x] **Build comprehensive prompt library with 4 variants per task ([prompts/](src/Traction/prompts/))** (Jan 2026)
- [x] **Complete evaluation study with GPT-4o/GPT-4o-mini/GPT-3.5-turbo** (Jan 2026)
- [x] **Implement PROMPT_REGISTRY for automatic schema-prompt mapping** (Jan 2026)

**In Progress:**
- [ ] Scale fine-tuning pipeline to additional policy domains
- [ ] Integrate external sector stance analysis into unified CLI
- [ ] Optimize prompt strategies based on latest evaluation results
- [ ] Extend time series coverage with 2025-2026 Article IV reports

## Citation

If you use this code in your research, please cite:
```
IMF AI Tools for Interim Surveillance Review (2025)
https://github.com/[repo-url]
```

## License

[Add appropriate license information]

## Contact

For questions or issues, please contact [contact information] or open an issue on GitHub.
