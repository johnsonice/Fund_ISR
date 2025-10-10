# AI Tools for 2025 Interim Surveillance Review

## Overview
AI-powered text analysis pipeline for Article IV consultation reports. Automatically classifies paragraphs into macroeconomic topics (Economic Outlook, Monetary Policy, Fiscal Stance, Financial Stability, External Stance) and extracts policy stance/agreement metrics using OpenAI language models.

## Key Features
- **Topic Classification**: Classify paragraphs into 6 predefined macroeconomic categories with confidence scores
- **Stance Detection**: Extract monetary/fiscal policy stance (tightening/loosening/neutral) from Staff Appraisal and Authorities' Views
- **Agreement Analysis**: Identify staff-authorities agreement/disagreement on policy recommendations
- **Batch Processing**: Cost-effective large-scale analysis using OpenAI Batch API
- **Structured Output**: Pydantic-validated responses with paragraph and document-level aggregations

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

- **`libs/`** - Reusable utilities (LLM wrappers, prompt loaders, text processing)
- **`src/Traction/`** - Main pipeline: preprocessing, topic classification, stance/agreement extraction, aggregation
- **`src/Traction/prompts/`** - Pydantic schemas and markdown prompt templates (4 variants per task: simple, with_definitions, few_shot, chain_of_thought)
- **`notebooks/Traction/`** - Evaluation notebooks and demos
- **`src/Others/`** - Experimental scripts

## Pipeline Overview

**Data Flow:**
1. XML documents → `data_preprocess.py` → paragraph CSV
2. Paragraphs → `topic_identification*.py` → classified CSV with confidence scores
3. Classified data → `paragraph_back2_doc.py` → document-level summaries

**Key Scripts:**
- `data_preprocess.py` - Extract paragraphs from XML (Staff Appraisal, Buff Statement, Staff Report, Authorities' Views)
- `topic_identification.py` / `topic_identification_batch.py` - Topic classification (async or batch)
- `paragraph_back2_doc.py` - Aggregate to document level

**Topic Categories:**
1. Economic Outlook (GDP, growth, forecasts)
2. Monetary Policy (interest rates, inflation, central bank)
3. Fiscal Stance (spending, debt, budget)
4. Financial Stability (banking, financial risks)
5. External Stance (balance of payments, exchange rates)
6. Other

## Usage

**Complete Pipeline:**
```bash
conda activate traction

# Step 1: Extract paragraphs from XML
python src/Traction/data_preprocess.py

# Step 2: Classify topics (choose one)
python src/Traction/topic_identification.py              # Async (fast for small batches)
python src/Traction/topic_identification_batch.py        # Batch API (cost-effective, large scale)
python src/Traction/topic_identification.py --test-mode  # Test mode (sample data)

# Step 3: Aggregate to document level
python src/Traction/paragraph_back2_doc.py
```

**Outputs:**
- `output/df_paragraphs.csv` - Paragraph-level text
- `output/paragraph_with_sector*.csv` - Classified paragraphs with confidence scores
- `output/document_by_type_sector.csv` - Document-level aggregations

**Evaluation:**
Use `notebooks/Traction/evaluate_fiscal_monetray_pipeline.ipynb` to run evaluations. Results in `notebooks/Traction/evaluation_results.md`.

## Model Selection Guide

Based on evaluation results (`notebooks/Traction/evaluation_results.md`):

**Agreement Classification:**
- GPT-5 + Few Shot: 74.74% (best)
- GPT-5-Mini + Few Shot: 71.97% (cost-effective, -2.8%)
- GPT-5-Nano + Few Shot: 66.44% (budget, -8.3%)

**Stance Classification:**
- GPT-5 + Few Shot: 74.05% (best, strongly recommended)
  - Current stance: 78.55%, Future stance: 69.55%
- GPT-5-Mini + Few Shot: 65.40% (-8.6%, significant drop)

**Recommendations:**
- Always use `few_shot` prompts (consistently best across all models/tasks)
- GPT-5 worth premium for stance tasks (larger performance gap vs smaller models)
- Avoid `with_definitions` prompts (consistently worst performer)

## Tasks

**Completed:**
- [x] ~~Replicate Xiaorui's topic tagging workflow with full reproducibility~~
- [x] ~~Implement monetary and fiscal policy stance extraction with agreement metrics~~
- [x] ~~Extend document ingestion to cover 2024-2025 Article IV reports~~
- [x] ~~Develop External Sector methodology for balance/exchange rate analysis~~

**Pending:**
- [ ] Investigate performance gap in stance prediction (GPT-4o vs GPT-4o-mini: -8.6%)
- [ ] Build complete pipeline for fiscal policy stance and agreement classification
- [ ] Collect and process Article IV reports from 2023-2025 to extend time series
- [ ] Reproduce all data visualizations with updated results
