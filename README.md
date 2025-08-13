# AI Tools for 2025 Interim Surveillance Review

## Overview
This project utilizes AI tools for the 2025 interim surveillance review. The project is structured into various sections, each focusing on a specific aspect of the setup and usage of these tools.

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
   - You are also advised to have a openai_key.json file udner [root_folder]/key/openai_key.json     
     ```
        {
           "ISR": {
            "API_KEY": "xxxxxxxxx"
            }
        }
     ```

## Folder Structure

- **`libs` Directory:**
  - Contains a collection of utility functions designed for the OpenAI assistant.

- **`notebooks` Directory:**
  - Includes various testing files for different functions, allowing for experimentation and validation of the tools.

- **`src` Directory:**
  - Hosts code snippets and scripts necessary to complete the required tasks for the review.

### Traction Submodule (`src/Traction`)
Focused pipeline for extracting, structuring, and classifying Article IV (AIV) report text.

Key components:
- `config.py`: Defines `data_dir` and `raw_xml_dir` (auto OS switch). Override paths if running on a different machine.
- `data_preprocess.py`:
  - Scans raw XML folders (`ArticleIV_xml_updated/results_v2` & `results_v5`).
  - Extracts Staff Appraisal, Buff Statement, Staff Report body paragraphs, and Authorities' Views.
  - Produces document-level CSV (`df_aiv.csv`) and paragraph-level CSV (`df_paragraphs.csv`).
- `paragraph_topic_identification.py`:
  - Loads `df_paragraphs.csv` and a prompt (`prompts/topic_classification.md`).
  - (Currently TEST_MODE=True, samples 100 paragraphs). Extend to batch LLM inference using utilities in `libs/` (e.g. `BatchAsyncLLMAgent`).
- `prompts/topic_classification.md`: Prompt template with macro topic taxonomy (Economic Outlook, Monetary Policy, Fiscal Stance, Financial Stability, External Stance, Other).
- `log/` subtree: Experiment run logs by user/date.

Expected external data layout (default Linux example):
```
~/data/Fund/CSR/Tractions/
  ├─ ArticleIV_xml_updated/
  │    ├─ results_v2/
  │    └─ results_v5/
  ├─ text_collection/IMF_Main_MetaData_*.xlsx
  └─ output/ (created automatically)
```

### Running the Traction Pipeline
1. Ensure raw XML and metadata Excel exist at the paths above (adjust `config.py` or inline overrides in scripts if needed).
2. Run preprocessing:
   ```bash
   python src/Traction/data_preprocess.py
   ```
   Outputs:
   - `output/df_aiv.csv` (document-level)
   - `output/df_paragraphs.csv` (paragraph-level)
3. (Optional) Run topic classification prototype:
   ```bash
   python src/Traction/paragraph_topic_identification.py
   ```
   Modify `TEST_MODE` to `False` and integrate batching + model calls for full runs.

Output columns (selected):
- Document-level: `paragraphs_sa`, `paragraphs_bu`, `paragraphs_sr` (staff report), `paragraphs_av` (authorities' views), verification flags.
- Paragraph-level: `Print ISBN`, `text`, `type` (staff, buff, staff_a, buff_a), `av_uncertain`.

Logging: Per-user experiment logs stored under `src/Traction/log/<USER>/<YYYY-MM-DD>/`.

## To-Do List

- [ ] Task 1: Replicate Xiaorui's topic tagging workflow (end-to-end reproducible scripts, taxonomy alignment, matching output structure).
- [ ] Task 2: Replicate monetary and fiscal policy stance extraction plus staff stance and authorities' agreement metrics (parity with Xiaorui’s reported results).
- [ ] Task 3: Extend ingestion + preprocessing to include additional AIV documents covering 2024 and 2025 (update metadata + re-run pipelines).
- [ ] Task 4: Extend methodology to External Sector (external balance, exchange rate, reserves) with comparable classification and stance/agreement outputs.

## Contact
- chuang@imf.org
