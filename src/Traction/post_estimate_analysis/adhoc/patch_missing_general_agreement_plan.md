# Ad-hoc patch: score the 37 missing docs and append to `df_documents_general_v2.csv`

## Goal (as requested)

1. Take **only the missing documents** (the ones absent from the general-agreement
   output), run the **zero-shot general-agreement (v2)** inference on them — which
   produces both the 7 `Agreement_*` scores **and** the 6 `*_Sector` disagreement
   lists in one model call.
2. Append the results into
   `/data/home/xiong/data/Fund/CSR/Tractions/output/adhoc/general_agreement_v2/df_documents_general_v2.csv`
   so that file grows from 981 → 1018 rows.

**No re-run of topic classification / step-04 / the full corpus.** This is a
targeted top-up of just the missing rows.

## Key facts established (verified, not assumed)

- **The general-agreement step needs NO topic classification.** It reads
  `df_documents.csv` (`Print ISBN, staff, buff, country, year, publication_date`)
  — one row per doc with full staff & authority text — and the **model itself
  emits** both `Agreement_*` scores and `*_Sector` lists. So "proper sector
  classification" is an *output* of this same call, not a prerequisite. Confirmed
  in [inference_general_agreement.py](../../inference_general_agreement.py) (reads
  `staff`/`buff`, drops rows missing either; `column_mapping =
  TASK_COLUMN_MAPPINGS['agreement']`).
- **Target file schema** (`df_documents_general_v2.csv`, 981×21): `index,
  Print ISBN, staff, buff, country, year, publication_date, id,
  Agreement_General, Agreement_Monetary, Agreement_Fiscal, Agreement_External,
  Agreement_Financial, Agreement_Real, Agreement_Other, Monetary_Sector,
  Fiscal_Sector, External_Sector, Financial_Sector, Real_Sector, Other_Sector`.
  This is the **v2** schema (has `Agreement_Other`/`Other_Sector`) → we must use
  `--prompt-variant simple_v2` (the script's default) to match it.
- **Which docs are missing:** the 38 that are in `df_fin_reg_core_merged.csv` but
  not in `df_documents_general_merged.csv`. Of these:
  - **37** are 2024 Article IV reports with **complete staff+buff text** available
    in
    `incremental_update/05252026_update/df_documents_incremental.csv`
    (schema identical to `df_documents.csv`). → **patchable.**
  - **1** — `9781484305775` (CEMAC 2017, a regional aggregate) — its text **does**
    exist (43 paragraphs in
    `06_07_2026_update/df_paragraphs_incremental.csv`), but **all 43 are
    staff-side** (`staff`/`staff_a`); it has **zero buff/authority paragraphs**.
    The general-agreement task is bilateral (staff vs authorities) and
    `inference_general_agreement.py` drops any row missing either side, so this
    doc is **structurally un-scoreable** — that is the very reason it was missing
    all along. We reconstruct its staff/buff from paragraphs, feed it in, and let
    the standard staff-and-buff filter drop it; it is **reported in
    `patch_excluded_docs.csv` with reason `no_buff_text`**, not fabricated.
- **Why they were missing:** the topic-classification + general-agreement runs
  were last executed on a pre-2024 981-doc snapshot; the doc backbone was later
  refreshed with these 2024 reports but the general-agreement step was never
  re-run over them.

## Inputs / outputs at a glance

| Role | Path |
|---|---|
| Text source for the 37 docs | `…/incremental_update/05252026_update/df_documents_incremental.csv` |
| Target to append into | `…/output/adhoc/general_agreement_v2/df_documents_general_v2.csv` |
| Inference entry point | `src/Traction/inference_general_agreement.py` |
| Prompt variant | `simple_v2` (v2 schema — matches target) |
| Model | `gpt-5.4-mini-2026-03-17` (same as the pipeline default in `07_*`/`run_general_agreement.sh`) |

## Implementation plan

All work lives in a single new ad-hoc script under
`src/Traction/post_estimate_analysis/adhoc/` (kept out of the numbered pipeline).
Backups are taken before the target file is touched.

### Step 0 — Backup (safety)
- Copy the target to
  `df_documents_general_v2.prepatch.bak.csv` in the same dir. Never overwrite the
  original in place without this.

### Step 1 — Build the "missing docs" input CSV
A small script `patch_missing_general_agreement.py`:
1. Load `df_fin_reg_core_merged.csv` and `df_documents_general_merged.csv`
   (06_07_2026_update); compute the gap ISBN set (normalized keys, strip `.0`).
2. Load `05252026_update/df_documents_incremental.csv`; select the gap rows.
3. Keep exactly the 6 input columns
   (`index, Print ISBN, staff, buff, country, year, publication_date` — drop the
   helper `isbn`). Assert: 37 rows, all with non-empty `staff` **and** `buff`.
4. Log & drop any gap ISBN with no text (the 1 CEMAC doc) — write the excluded
   list to `patch_excluded_docs.csv` for transparency.
5. Write `df_documents_missing_input.csv` (37 rows) into
   `adhoc/general_agreement_v2/`.

### Step 2 — Run zero-shot general-agreement (v2) on just those 37
Invoke the existing inference script against the 37-row input, writing to a
**separate** results file (not the target yet):

```bash
/data/home/xiong/miniconda3/envs/traction/bin/python \
  src/Traction/inference_general_agreement.py \
  --data-file  …/adhoc/general_agreement_v2/df_documents_missing_input.csv \
  --output-dir …/adhoc/general_agreement_v2 \
  --output-file df_documents_general_v2_patch.csv \
  --model gpt-5.4-mini-2026-03-17 \
  --prompt-variant simple_v2 \
  --submit --post-process \
  --max-output-tokens 16384
```

- This produces `df_documents_general_v2_patch.csv` (~37 rows, full v2 schema:
  8 id/meta cols + 7 `Agreement_*` + 6 `*_Sector`).
- Uses the OpenAI Batch API (submits a batch, waits, post-processes) — same path
  the pipeline already uses; needs `OPENAI_API_KEY` in `.env`.
- ⚠ The script re-assigns `id = row index` (0..36) on its own input. That's fine
  for the patch file in isolation, but on append the `id` column will collide with
  the target's existing 0..980. **Step 3 renumbers `id` on concat** so it stays a
  unique running index (or we simply leave `id` as-is and document that it is a
  per-file row ordinal, not a global key — `Print ISBN` is the real key).

### Step 3 — Append to the v2 target
In the same script (a `--append` phase, run after the batch completes):
1. Load target `df_documents_general_v2.csv` (981) and the patch
   `df_documents_general_v2_patch.csv` (37).
2. **Guard against dupes:** drop any patch ISBN already present in the target
   (should be 0), so re-runs are idempotent.
3. Align columns to the target's exact order; `concat`.
4. Reset `id` to a clean running `0..N-1` over the combined frame (keeps it a
   valid ordinal; `Print ISBN` remains the join key downstream).
5. Write back to `df_documents_general_v2.csv` (now 1018 rows).
6. Print a summary: rows before/after, #appended, #skipped-dupes, #excluded.

### Step 4 — Verify
- `df_documents_general_v2.csv` row count = 981 + 37 = **1018**; unique ISBN =
  1018; the 37 gap ISBNs now present; all have non-null `Agreement_General`.
- Spot-check 2–3 appended rows: scores in the expected integer range, `*_Sector`
  values are lists/strings as in existing rows, no all-null rows.
- Confirm the 1 excluded doc (`9781484305775`) is listed in
  `patch_excluded_docs.csv` and absent from the output.

## Artifacts produced

| File (in `adhoc/general_agreement_v2/`) | Purpose |
|---|---|
| `df_documents_general_v2.prepatch.bak.csv` | pre-patch backup of the target |
| `df_documents_missing_input.csv` | 37-row inference input |
| `df_documents_general_v2_patch.csv` | raw inference output for the 37 |
| `patch_excluded_docs.csv` | the 1 doc with no text (CEMAC 2017) |
| `df_documents_general_v2.csv` | **updated target: 981 → 1018 rows** |
| `patch_missing_general_agreement.py` | the driver script (build-input / append phases) |

## Open questions before I run it

1. **Model** — use `gpt-5.4-mini-2026-03-17` (pipeline default) so the 37 new rows are scored
   by the same model as the existing 981? (Recommended, for consistency.)
2. **The 1 text-less doc** (`9781484305775`, CEMAC 2017) — exclude it (my plan) or
   do you want me to try to source its staff/buff text from the paragraph files
   first?
3. **`id` column** — renumber to a clean `0..1017` on append (my plan), or leave
   the patch rows' `id` as their own 0..36? (`Print ISBN` is the real key either
   way.)
```
