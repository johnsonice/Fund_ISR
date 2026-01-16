# AI Tools for 2025 Interim Surveillance Review

## Overview
Complete end-to-end AI pipeline for analyzing IMF Article IV consultation reports. Automatically extracts macroeconomic topics, classifies policy stances (monetary/fiscal), detects staff-authorities agreement/disagreement, and generates publication-ready visualizations using OpenAI language models.

**Pipeline Coverage:** XML extraction → Topic classification → Stance/agreement inference → Statistical analysis → Visualization

## Key Features
- **Topic Classification**: Classify paragraphs into 6 macroeconomic categories with confidence scores
- **Stance Detection**: Extract monetary/fiscal policy stance (current + future direction) for IMF staff and authorities
- **Agreement Analysis**: Detect staff-authorities agreement/disagreement with specific disagreement area extraction
- **Production CLI**: Unified interface (`inference_agreement_stance.py`) for both monetary and fiscal domains
- **Batch Processing**: Cost-effective large-scale analysis using OpenAI Batch API
- **Post-Estimation Analysis**: Income group classification, trend analysis, and publication-quality charts
- **Prompt Library**: 17+ prompts with 4 variants per task (simple, with_definitions, few_shot, chain_of_thought)
- **Fine-Tuning Support**: Pipeline for fine-tuning on domain-specific stance classification

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

- **`libs/`** - Reusable utilities (LLM wrappers, prompt loaders, batch processing)
- **`src/Traction/`** - Main pipeline modules:
  - `data_preprocess.py` - XML paragraph extraction
  - `topic_identification*.py` - Topic classification (async/batch)
  - `paragraph_back2_doc.py` - Document-level aggregation
  - `inference_agreement_stance.py` - Production stance/agreement inference
  - `llm_batch_process_utils.py` - Flexible message building utilities
  - `scripts/` - Batch execution shell scripts
  - `post_estimate_analysis/` - Visualization toolkit
  - `train_eval/` - Fine-tuning pipeline
- **`src/Traction/prompts/`** - Pydantic schemas and markdown prompt templates
  - 4 variants per task: simple, with_definitions, few_shot (recommended), chain_of_thought
- **`notebooks/Traction/`** - Evaluation notebooks, inference demos, interactive analysis
- **`src/Others/`** - Experimental scripts

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
- `data_preprocess.py` - Extract paragraphs from XML
- `topic_identification*.py` - Topic classification (async or batch)
- `paragraph_back2_doc.py` - Aggregate to document level
- `inference_agreement_stance.py` - Unified stance/agreement inference CLI
- `scripts/run_all.sh` - Parallel execution orchestrator
- `post_estimate_analysis/data_vis_utils.py` - Visualization utilities

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

```bash
# Run all 4 tasks in parallel (monetary/fiscal × stance/agreement)
bash src/Traction/scripts/run_all.sh

# Individual scripts with custom prompt variant
PROMPT_VARIANT=few_shot bash src/Traction/scripts/run_monetary_stance.sh
```

**Available Tasks:** `agreement` (staff-authorities), `stance` (policy direction)
**Available Domains:** `monetary` (restrictive/neutral/accommodative), `fiscal` (contractionary/neutral/expansionary)

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

**Recommended: GPT-4o** (based on [evaluation_results_replication.md](src/Traction/evaluation_results_replication.md))

| Task | Best Model + Prompt | Accuracy |
|------|---------------------|----------|
| Monetary Agreement | GPT-4o + Simple Short | 73.7% |
| Monetary Stance | GPT-4o + Few-shot | 64-70% |
| Fiscal Agreement | GPT-4o + Chain of Thought | 70.0% |
| Fiscal Stance | GPT-4o + Simple | 77.8% |

**Key Findings:**
- GPT-4o consistently outperforms GPT-4o-mini across all tasks
- Merging unclear/irrelevant labels improves stance accuracy by 5-13%
- Optimal prompt varies by task (no single "best prompt")
- Fine-tuning can target >75% accuracy (see [train_eval/](src/Traction/train_eval/))

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

## Prompt Library

The [prompts/](src/Traction/prompts/) directory contains 17+ markdown templates:

**Prompt Variants (4 per task):**
- `simple` - Minimal instructions
- `with_definitions` - Detailed category definitions
- `few_shot` - Includes examples (often performs best)
- `chain_of_thought` - Adds reasoning step

**Available Prompts:** `topic_classification`, `monetary_stance_*`, `monetary_agreement_*`, `fiscal_stance_*`, `fiscal_agreement_*`

**PROMPT_REGISTRY** in [schema.py](src/Traction/prompts/schema.py) maps prompt keys to files and Pydantic response models.

## Project Status

**To Do:**
- [ ] Experiment fine-tuned pipeline with the formalized prompts for both monetary and fiscal domains
- [ ] Extend data range to current (2025-2026 Article IV reports)
- [ ] Explore training strategies beyond SFT (e.g., RFT, RLHF)

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
