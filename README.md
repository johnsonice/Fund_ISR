# AI Tools for 2025 Interim Surveillance Review

## Overview
Complete end-to-end AI pipeline for analyzing IMF Article IV consultation reports. Automatically extracts macroeconomic topics, classifies policy stances (monetary/fiscal), detects staff-authorities agreement/disagreement, and generates publication-ready visualizations using OpenAI language models.

**Pipeline Coverage:** XML extraction → Topic classification → Stance/agreement inference → Statistical analysis → Visualization

## Key Features
- **Topic Classification**: Classify paragraphs into 6 predefined macroeconomic categories with confidence scores (0-100)
- **Stance Detection**: Extract monetary/fiscal policy stance (current + future direction) for both IMF staff and country authorities
- **Agreement Analysis**: Identify staff-authorities agreement/disagreement with specific disagreement area extraction
- **Production-Ready Inference**: Unified CLI (`inference_agreement_stance.py`) for both monetary and fiscal domains
- **Batch Processing**: Cost-effective large-scale analysis using OpenAI Batch API (50% cost reduction)
- **Post-Estimation Analysis**: Income group classification, trend analysis, and publication-quality charts
- **Structured Output**: Pydantic-validated responses with paragraph and document-level aggregations
- **Fine-Tuning Support**: Complete pipeline for fine-tuning GPT-5-mini on domain-specific stance classification

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
  - `post_estimate_analysis/` - Visualization toolkit (NEW)
  - `train_eval/` - Fine-tuning pipeline for GPT-5-mini
- **`src/Traction/prompts/`** - 17+ Pydantic schemas and markdown prompt templates
  - 4 variants per task: simple, with_definitions, **few_shot** (recommended), chain_of_thought
  - Supports: topic classification, monetary/fiscal stance, monetary/fiscal agreement
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
- `post_estimate_analysis/data_vis_utils.py` - Visualization utilities (sector-agnostic, composable)

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
```

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

**Fine-tune GPT-5-mini for stance classification:**
```bash
cd src/Traction/train_eval
python run_pipeline.py  # Complete pipeline (prepare → train → evaluate)

# Or step-by-step
python prepare_data.py
python finetune.py
python evaluate.py
```

Results saved to `notebooks/Traction/evaluation_results.md`.

## Model Selection Guide

**Recommended: GPT-5-mini (August 2025 release) - Best balance of cost and performance**

Based on evaluation results with previous generation models (`notebooks/Traction/evaluation_results.md`):

### Agreement Classification
- **GPT-5** + Few Shot: ~75-78% accuracy (premium, +3-5% over GPT-5-mini)
- **GPT-5-mini** + Few Shot: ~72-75% accuracy (RECOMMENDED default)
- **GPT-5-nano** + Few Shot: ~66-70% accuracy (budget option)

### Stance Classification
- **GPT-5** + Few Shot: ~74-78% accuracy (premium, +8-10% over GPT-5-mini)
  - Current stance: 78.55%, Future stance: 69.55%
- **GPT-5-mini** + Few Shot: ~65-70% accuracy (recommended baseline)
- **Fine-tuned GPT-5-mini**: Target >75% accuracy (see `src/Traction/train_eval/`)

### Model Selection Strategy

| Use Case | Recommended Model | Rationale |
|----------|------------------|-----------|
| **Agreement detection** | `gpt-5-mini` + few_shot | Cost-effective, 72-75% accuracy sufficient |
| **Stance classification** | Fine-tuned `gpt-5-mini` | Best cost/performance after fine-tuning (>75%) |
| **High-stakes analysis** | `gpt-5` + few_shot | Premium accuracy (74-78%) when precision is critical |
| **Large-scale processing** | Batch API + `gpt-5-mini` | 50% cost reduction for bulk inference |
| **Budget constraints** | `gpt-5-nano` + few_shot | 66-70% accuracy, lowest cost |

**Model IDs (August 2025):**
- `gpt-5-mini-2025-08-07` - Default for most tasks
- `gpt-5-2025-08-07` - Premium for complex reasoning
- `gpt-5-nano-2025-08-07` - Budget option

**Key Findings:**
- ✅ Always use `few_shot` prompts (consistently best across all models/tasks)
- ✅ GPT-5-mini is the recommended default (best cost-performance tradeoff)
- ✅ Fine-tuning GPT-5-mini improves stance accuracy by ~10% (+$0.50-2.00 per training run)
- ⚠️ Avoid `with_definitions` prompts (consistently worst performer)
- ⚠️ GPT-5 premium worth it for stance tasks if budget allows (+8-10% accuracy)

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

## Project Status

**Completed:**
- [x] ~~Replicate Xiaorui's topic tagging workflow with full reproducibility~~
- [x] ~~Implement monetary and fiscal policy stance extraction with agreement metrics~~
- [x] ~~Extend document ingestion to cover 2024-2025 Article IV reports~~
- [x] ~~Develop External Sector methodology for balance/exchange rate analysis~~
- [x] **Build production pipeline for stance and agreement classification (`inference_agreement_stance.py`)**
- [x] **Implement flexible batch processing utilities for multi-column prompts**
- [x] **Create post-estimation analysis toolkit with publication-ready visualizations**
- [x] **Develop fine-tuning pipeline for domain-specific stance classification**
- [x] **Build complete pipeline for fiscal policy stance and agreement classification**
- [x] **Reproduce all data visualizations with updated results**

**In Progress:**
- [ ] Investigate fiscal sector prompts and performance (comparison with monetary sector)
- [ ] Extend time series coverage with 2023-2025 Article IV reports
- [ ] Scale fine-tuning pipeline to additional policy domains
- [ ] Integrate external sector stance analysis into unified CLI

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
