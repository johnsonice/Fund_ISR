# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

### Evaluation & Development

- **Evaluation Pipeline**: `notebooks/Traction/evaluate_fiscal_monetray_pipeline.ipynb`
  - Function: `evaluate_prompt_and_model(prompt_key, model_name, data_dir, use_full_dataset=True)`
  - Supports monetary/fiscal stance and agreement tasks
  - Results in `notebooks/Traction/evaluation_results.md`
- Run Jupyter notebooks from `notebooks/Traction/` for demos and experimentation
- Logs are automatically created at: `src/Traction/log/{USER}/{YYYY-MM-DD}/Exp-{HH:MM}.log`

## Architecture Overview

### Directory Structure

- **`libs/`**: Reusable utility modules
  - `llm_factory_openai.py`: OpenAI API wrapper with async batch processing (BatchAsyncLLMAgent)
  - `prompt_utils.py`: Prompt template loader
  - `llm_utils*.py`: LLM interaction utilities with retry logic
  - `clean_text_utils.py`, `utils_pdf.py`, `utils.py`: Text/PDF/general utilities

- **`src/Traction/`**: Main processing pipeline for Article IV documents
  - **Data flow:** XML → `data_preprocess.py` → paragraphs CSV → `topic_identification*.py` → classified CSV → `paragraph_back2_doc.py` → document-level summaries

- **`src/Others/`**: Experimental scripts and one-off analyses

- **`notebooks/`**: Jupyter notebooks for development and testing

### Core Pipeline Components

**1. Configuration (`src/Traction/config.py`):**
- Cross-platform path configuration (Windows/Linux)
- Data directory paths differ by OS: Windows uses OneDrive paths, Linux uses `~/dev/Fund/CSR/Tractions/`

**2. Data Preprocessing (`src/Traction/data_preprocess.py`):**
- Parses XML documents using BeautifulSoup
- Extracts: Staff Appraisal, Buff Statement, Staff Report body, Authorities' Views
- Outputs paragraph-level data ready for classification

**3. Topic Classification:**
- Uses OpenAI LLMs with structured output (Pydantic validation)
- Two implementations: async (`topic_identification.py`) and batch API (`topic_identification_batch.py`)
- Both use shared utilities in `llm_batch_process_utils.py`

**4. Schema & Prompts (`src/Traction/prompts/`):**
- `schema.py`: Pydantic models and PROMPT_REGISTRY mapping prompt keys to files/models
  - `TopicResponse`: Topic classification with confidence scores (0-100)
  - `MonetaryStanceResponse`, `FiscalStanceResponse`: Policy stance classification
  - `MonetaryAgreementResponse`, `FiscalAgreementResponse`: Agreement detection
  - Chain-of-thought variants include reasoning field
- Markdown prompt templates: 4 variants per task (simple, with_definitions, few_shot, chain_of_thought)
- **Recommended**: Use few_shot prompts for best performance (see `notebooks/Traction/evaluation_results.md`)

**5. Post-Processing (`src/Traction/paragraph_back2_doc.py`):**
- Aggregates paragraph-level classifications to document-level summaries
- Creates binary dummy variables for topics with confidence > 30%

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
- Recommended models: `gpt-4o` (best accuracy), `gpt-4o-mini` (cost-effective), `gpt-4o-nano` (budget)

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

**After classification:**
- `output/paragraph_with_sector.csv` (async) or `output/paragraph_with_sector_batch.csv` (batch)
  - Columns: original data + confidence scores for each topic + binary dummies

**After aggregation:**
- `output/document_by_type_sector.csv`: Document-level topic summaries

### Key Design Patterns

1. **Async Processing:** Uses asyncio and `tqdm.asyncio` for concurrent API calls with progress bars
2. **Structured Output:** All LLM responses validated against Pydantic schemas
3. **Batch API:** Cost-effective processing for large datasets via OpenAI Batch API
4. **Wide Format Conversion:** Pivot long-form results to wide DataFrame with topic columns
5. **Logging:** Automatic timestamped logs organized by user and date

## Model & Prompt Selection Guide

Based on evaluation results (`notebooks/Traction/evaluation_results.md`):

**Agreement Classification:**
- GPT-4o + Few Shot: 74.74% accuracy (best)
- GPT-4o-mini + Few Shot: 71.97% accuracy (cost-effective, -2.8%)
- GPT-4o-nano + Few Shot: 66.44% accuracy (budget, -8.3%)

**Stance Classification:**
- GPT-4o + Few Shot: 74.05% accuracy (best, strongly recommended)
- GPT-4o-mini + Few Shot: 65.40% accuracy (significant drop, -8.6%)

**Key Findings:**
- Always use few_shot prompts (consistently best across all tasks)
- GPT-4o worth premium for stance tasks (larger performance gap)
- Avoid "with_definitions" prompts (consistently worst)
