## Documentation

### Data Extraction

- Raw data are in folder: `C:\Users\chuang\OneDrive - International Monetary Fund (PRD)\AI tools\Data\ArticleIV_xml_updated`
- Combine all XML files in the folder and match them with the metadata file
- Staff Appraisal extraction steps:
  
  1. Scans all `<sec>` elements
  2. Looks for a `<title>` whose text matches `STAFF_APPRAISAL_RE`
  3. Removes unwanted visual-only tags (`<fig>`, `<table-wrap>`)
  4. Trims the section at the last numbered paragraph (e.g., paragraphs starting with "1", "2", ...)
  5. Returns:
     - The resulting section HTML (as a string)
     - A flattened list of paragraph texts plus list-item texts

- Buff Statement extraction steps:
    - Path 1 (Title-based): If any <article-title> inside <body> literally contains “statement by” or “statement on” (case-insensitive), we treat the entire <body> as the target and return all non-empty paragraph texts.

    - Path 2 (Lead-paragraph-based): If the titles don’t say “statement by/on”, we look for the first paragraph whose text starts with that phrase (using STATEMENT_RE: ^statement (by|on)\b). If found, we return the text from every subsequent paragraph after that “lead” paragraph.

- Turn raw data into df:
    * Combine seven extraction dictionaries into a single DataFrame and reset index.
    * Remove rows with keys starting with `spr_`.
    * Rename columns to descriptive names for staff/buff filenames, texts, and paragraphs.
    * Add `staff_verified` and `buff_verified` flags for non-empty paragraph lists.
    * Merge in metadata fields from `df_meta` on `Print ISBN`.
    * Build a combined title from multiple title fields.
    * Flag rows with titles containing `"statement by"` as `has_buff`.
    * Null out “buff” paragraphs that only state authorities’ views “do not alter/change” the staff appraisal.
    * Recalculate `buff_verified` after nulling.
    * Manually correct `Year from title` for specific ISBNs. (why not do it for all?)
    * Drop the temporary combined title column.

- Extract extra staff views VS authorities views:
    * Loop through each row with a valid `text_staff` value.
    * Parse the HTML, removing `<fig>`, `<table-wrap>`, and `<boxed-text>` elements.
    * Extract `<sec>` sections between “contents” and “staff appraisal” headings.
    * Flatten nested sections into a single list of sections to process.
    * Determine split method (`rule_type`) based on presence and formatting of “authorities” content.
    * Split paragraphs into **staff views** (`paragraphs_sr`) and **authorities’ views** (`paragraphs_av`) according to the rule.
    * Flag entries as `av_uncertain` when using the fallback split method (rule 2).

- Merge text data with all fundmental data 

- Identify topics for each paragraphs:
    - convert doc data into paragraphs
        * Convert paragraph columns (`paragraphs_sa`, `paragraphs_bu`, `paragraphs_sr`, `paragraphs_av`) from string representations to Python lists.
        * Expand each paragraph list into a long-form DataFrame with one row per paragraph, tagged by `Print ISBN` and a `type` label:
        * `'buff'` → `paragraphs_bu`
        * `'staff'` → `paragraphs_sa`
        * `'buff_a'` → `paragraphs_av` (authorities’ views)
        * `'staff_a'` → `paragraphs_sr` (staff views)
        * Concatenate all paragraph rows into a single DataFrame.
        * Remove exact duplicate rows.
        * Flag rows with NaN or very short text (≤ 100 characters) in a `to_drop` column.
        * Merge in `av_uncertain` from the original DataFrame by ISBN.
        * Set `av_uncertain = False` for paragraph types `'staff'` and `'buff'`, and fill missing flags with `False`.

    - use LLM to identify each paragraphs :
        * Loop through `df_paragraphs` rows where both `topic_labels` and `gpt_error` are NaN.
        * Send each paragraph (`row['text']`) to GPT-4o with a fixed system prompt defining IMF macroeconomic topics.


- Generate sample data for labeling:
    - 
