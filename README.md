# AI Tools for 2025 Interim Surveillance Review

## Overview
This project develops AI-powered tools for the 2025 Interim Surveillance Review (ISR), specifically focusing on automated text analysis and topic classification of Article IV (AIV) consultation reports. The system processes IMF staff reports, buff statements, and authorities' views to extract structured insights on macroeconomic topics including Economic Outlook, Monetary Policy, Fiscal Stance, Financial Stability, and External Stance.

## Key Features
- **Automated Document Processing**: Extract and structure text from XML-formatted IMF documents
- **AI-Powered Topic Classification**: Use OpenAI's language models to classify paragraphs into predefined macroeconomic topic categories
- **Batch Processing Support**: Handle large-scale document analysis through OpenAI's Batch API
- **Multi-format Output**: Generate both paragraph-level and document-level analytical outputs
- **Extensible Framework**: Modular design supporting additional topic categories and document types

## Environment Setup

1. **Create a New Virtual Environment:**
   - Set up a new virtual environment for this project.
   - Activate the environment and install required packages using:
     ```
     pip install -r requirements.txt
     ```

2. **Download Data:**
   - Data for this project should be downloaded and stored in the same root folder as this repository.
   - Use the following command to download the data (link will be provided soon):
     ```
     wget [link pending]
     ```
   - Provide your OpenAI API key via a `.env` file at the project root:
     ```
     OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
     ```

## Project Structure

### Core Directories

- **`libs/`** - Core utility libraries and components:
  - `llm_factory_openai.py`: OpenAI API client with async batch processing capabilities
  - `llm_utils.py` & variants: LLM interaction utilities with retry logic and logging
  - `prompt_utils.py`: Prompt template management and loading
  - `clean_text_utils.py`: Text preprocessing and cleaning functions
  - `utils_pdf.py`: PDF document processing utilities
  - `utils.py`: General-purpose helper functions

- **`src/`** - Main source code directory:
  - `Traction/`: Primary pipeline for Article IV document processing
  - `Others/`: Additional tools and experimental scripts for document analysis

- **`notebooks/`** - Jupyter notebooks for development and testing:
  - `Traction/`: Notebooks for the main pipeline development and demos
  - `Others/`: Experimental notebooks and one-off analyses

- **Configuration Files:**
  - `requirements.txt`: Python package dependencies
  - `.env`: Environment variables (OpenAI API key, etc.)

### Traction Pipeline (`src/Traction/`)
The main processing pipeline for Article IV consultation document analysis.

#### Core Components

**Configuration & Setup:**
- `config.py`: Cross-platform data directory configuration (Windows/Linux paths)

**Data Processing:**
- `data_preprocess.py`: XML document parser and text extractor
  - Processes Article IV documents from `results_v2/` and `results_v5/` folders
  - Extracts Staff Appraisal, Buff Statement, Staff Report body, and Authorities' Views
  - Outputs: `df_aiv.csv` (document-level), `df_paragraphs.csv` (paragraph-level)

**Topic Classification:**
- `topic_identification.py`: Asynchronous LLM-based topic classification
  - Uses OpenAI API with structured Pydantic schema validation
  - Processes paragraphs through predefined macroeconomic topic taxonomy
- `topic_identification_batch.py`: Batch processing variant for large-scale analysis
  - Leverages OpenAI Batch API for cost-efficient processing
  - Includes batch creation, submission, monitoring, and result processing
- `llm_batch_process_utils.py`: Utilities for batch processing workflows

**Schema & Prompts:**
- `prompts/schema.py`: Pydantic models defining structured LLM response format
  - `TopicLabel`: Individual topic classification with confidence scores
  - `TopicResponse`: Complete response structure with reasoning and topic labels
- `prompts/topic_classification.md`: Comprehensive prompt template with:
  - Six predefined topic categories (Economic Outlook, Monetary Policy, Fiscal Stance, Financial Stability, External Stance, Other)
  - Detailed definitions and key indicators for each topic
  - Classification guidelines and examples

**Post-processing:**
- `paragraph_back2_doc.py`: Aggregates paragraph-level classifications to document-level summaries

#### Data Requirements

The pipeline expects the following external data structure:
```
/data/home/xiong/data/Fund/CSR/Tractions/
├── ArticleIV_xml_updated/
│   ├── results_v2/          # XML documents (earlier version)
│   └── results_v5/          # XML documents (later version)
├── text_collection/
│   └── IMF_Main_MetaData_*.xlsx  # Document metadata
└── output/                  # Generated outputs (auto-created)
```

## Usage Guide

### Quick Start
1. **Environment Setup:**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Set up API key
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

2. **Run the Complete Pipeline:**
   ```bash
   # Step 1: Extract and preprocess documents
   python src/Traction/data_preprocess.py
   
   # Step 2: Classify topics (choose one method)
   # Option A: Async processing (faster for small batches)
   python src/Traction/topic_identification.py
   
   # Option B: Batch processing (cost-effective for large datasets)
   python src/Traction/topic_identification_batch.py
   
   # Step 3: Aggregate results to document level
   python src/Traction/paragraph_back2_doc.py
   ```

### Pipeline Outputs

**After Data Preprocessing:**
- `output/df_aiv.csv`: Document-level metadata and paragraph counts
- `output/df_paragraphs.csv`: Individual paragraphs ready for classification

**After Topic Classification:**
- `output/paragraph_with_sector.csv` (async) or `output/paragraph_with_sector_batch.csv` (batch)
  - Original paragraph data plus topic confidence scores (0-100)
  - Binary dummy variables for topics with confidence > 30%
  - Topics: Economic Outlook, Monetary Policy, Fiscal Stance, Financial Stability, External Stance, Other

**After Document Aggregation:**
- `output/document_by_type_sector.csv`: Document-level topic summaries by document type

### Logging and Monitoring
- Experiment logs: `src/Traction/log/{USER}/{YYYY-MM-DD}/Exp-{HH:MM}.log`
- Batch processing status and progress tracking included

## Technical Details

### Topic Classification Schema
The system classifies text into six predefined macroeconomic categories:

1. **Economic Outlook**: GDP growth, business cycle analysis, economic forecasts, recession risks
2. **Monetary Policy**: Interest rates, inflation targeting, central bank actions, quantitative easing
3. **Fiscal Stance**: Government spending, debt sustainability, fiscal consolidation, budget balance
4. **Financial Stability**: Banking sector health, financial sector risks, systemic risk assessment
5. **External Stance**: Balance of payments, exchange rates, external debt, trade balance
6. **Other**: Topics not covered by the above categories

### Dependencies
Key Python packages (see `requirements.txt` for complete list):
- `openai>=1.8.0`: OpenAI API client
- `pandas>=2.0.3`: Data manipulation and analysis
- `pydantic`: Data validation and schema enforcement
- `beautifulsoup4>=4.13.4`: XML/HTML parsing
- `tqdm>=4.66.1`: Progress bars
- `python-docx>=0.8.11`: Document processing
- `transformers>=4.32.1`: NLP model utilities

## Development Roadmap

### Current Tasks
- [ ] **Task 1**: Replicate Xiaorui's topic tagging workflow with full reproducibility
- [ ] **Task 2**: Implement monetary and fiscal policy stance extraction with agreement metrics
- [ ] **Task 3**: Extend document ingestion to cover 2024-2025 Article IV reports
- [ ] **Task 4**: Develop External Sector methodology for balance/exchange rate analysis

### Future Enhancements
- Multi-language support for non-English IMF documents
- Integration with additional document formats (PDF, DOCX)
- Real-time processing capabilities for new document releases
- Enhanced visualization tools for analytical outputs

## Contact
- chuang@imf.org
