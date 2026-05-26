# Incremental update workflow notes

This note is for agent reference when running the incremental Article IV update pipeline in this folder.

## Scripts in this folder

1. `01_data_preprocess_incremental.py`
   - Extract publication-level metadata from XML package folders.
   - Main output: raw metadata workbook.
2. `02_meta_data_postprocess.py`
   - Add title-derived fields and create the filtered AIV sheet.
   - Main output: postprocessed metadata workbook.
3. `03_incremental_aiv_update.py`
   - Build document- and paragraph-level incremental outputs.
   - **Important:** this step should consume a **clean filtered metadata workbook**, not the unchecked raw output from step 02.
4. `04_topic_identification_incremental.sh`
5. `05_paragraph_back2_doc_incremental.sh`
6. `06_inference_incremental.sh`
7. `07_merge_all_incremental.py`

## Required workflow

### Step 1
Run `01_data_preprocess_incremental.py` to generate the base metadata workbook from the XML package folders.

### Step 2
Run `02_meta_data_postprocess.py` to create:
- enriched metadata fields
- AIV flag
- filtered AIV sheet

If step 02 produces multiple metadata workbooks for different years, append the filtered AIV sheets from all yearly files into one combined filtered metadata file before QA. If there is only one metadata workbook, use its filtered AIV sheet as the QA input.

### Mandatory QA gate after steps 01-02
After step 02 finishes, the agent must **pause and verify the filtered metadata** before running step 03.

If there are multiple yearly metadata files, the QA must be performed on the **combined filtered metadata file**, not separately on each yearly file. If there is only one yearly file, perform QA on that single filtered file.

This verification is required to make sure **all country codes are properly matched**.

The authoritative reference for finalized country names and ISO3 codes is `src/Traction/docs/reference/country_meta_info.xlsx`.

Minimum checks:
- Confirm `Country Name from title` is populated correctly for AIV rows.
- Confirm `Primary Country Code` and `Primary Country Description` match the country identified from the title.
- Confirm `Primary Country Code` and `Primary Country Description` match **exactly** the corresponding `ISO3` and `Country` values in `src/Traction/docs/reference/country_meta_info.xlsx`.
- Treat `Primary Country Code` and `Primary Country Description` as the **finalized country fields** after QA.
- Compare title-derived country fields against original `countries` and `country_codes` values.
- Review rows with blank or suspicious country matches.
- Review rows where title parsing may fail because of aliases, alternate spellings, or formatting differences.
- Review any multi-country or ambiguous cases manually.
- Confirm `Print ISBN` remains unique for the filtered set.
- Example: Kosovo must use `Primary Country Code = KOS` and the matching country description from the reference workbook.

### Step 2.5 - Create clean metadata for step 03
The agent must create a **clean metadata workbook** for step 03 after QA is complete.

Rules for the clean metadata workbook:
- If there are multiple yearly metadata files, first append all filtered AIV sheets into a single combined metadata file.
- Use the combined filtered file as the QA source when multiple yearly files exist; otherwise use the single filtered file.
- Keep only the rows that should be processed by the incremental pipeline.
- Keep country fields corrected and finalized.
- Use `Primary Country Code` and `Primary Country Description` as the finalized country info, with values copied exactly from `src/Traction/docs/reference/country_meta_info.xlsx`.
- If country matching was fixed during QA, make sure the values used by step 03 are also corrected.
- Save the workbook with a clear name such as:
  - `<run_name>_metadata_filtered_clean.xlsx`
  - or `IMF_Main_MetaData_<date>_filtered_clean.xlsx`

Suggested intermediate naming for the pre-QA combined file:
- `<run_name>_metadata_filtered_combined.xlsx`
- or `IMF_Main_MetaData_<date>_filtered_combined.xlsx`

### Important compatibility note for step 03
`03_incremental_aiv_update.py` reads these fields directly from the metadata workbook:
- `Print ISBN`
- `title_full`
- `countries`
- `country_codes`
- `publication_date`
- optional `package_path`

Because of that, the clean metadata file for step 03 should not only contain reviewed derived columns; it should also have the final corrected values in `countries` and `country_codes` when needed.

In other words:
- `Primary Country Code` = finalized ISO3 country code from `src/Traction/docs/reference/country_meta_info.xlsx`
- `Primary Country Description` = finalized country name from `src/Traction/docs/reference/country_meta_info.xlsx`
- `country_codes` and `countries` should be updated as needed so they stay consistent with those finalized primary-country fields for step 03 consumption

Do **not** assume that the derived `Primary Country Code` column alone is enough for step 03.

### Step 3
Run `03_incremental_aiv_update.py` using the **clean filtered metadata workbook** produced after QA.

### Steps 4-7
Continue the downstream incremental pipeline only after step 03 succeeds.

## Agent operating rule

When executing this pipeline, the agent should follow this rule:

1. Run step 01.
2. Run step 02.
3. If multiple yearly metadata files exist, append their filtered AIV sheets into one combined metadata file.
4. Verify filtered metadata country matching on the resulting QA input file (the combined file if multiple yearly files exist, otherwise the single filtered file).
5. Create a clean metadata workbook for step 03.
6. Run step 03 using the clean metadata workbook.
7. Continue to later steps only after step 03 output looks valid.

## Stop conditions

The agent should stop and surface issues before step 03 if any of the following happens:
- missing or blank country codes in filtered AIV rows
- title country and mapped ISO3 country do not agree
- duplicate `Print ISBN` values in the filtered set
- metadata rows expected for processing are missing from the clean workbook
- uncertain country mapping that needs manual confirmation
