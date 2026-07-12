# Fix #2 — Montenegro extractor bug + data recovery

## Root cause (found & verified)

Montenegro 2025 (`9798229030076`) has its 3 article HTML files on disk (3 MB) but
extracted to empty text, yet `parse_status='success'`. Cause: the HTML extractor
(`data_preprocess_html.py`) identifies the staff report **only** by a "Staff
Appraisal / Staff Assessment" section heading. Montenegro's report is structured
**Context / Recent Developments / Outlook and Risks / Policy Discussions /
Annexes** — no separately-titled appraisal section. So:

- `_find_staff_report_html` found no matching heading → returned `None`.
- With `staff_path=None`, the extractor's write-block was skipped → **nothing
  written**, silently, for the whole package.

Scope check: of 220 HTML packages, 10 lack an appraisal heading, but **9 are old
stray ISBNs not in our document universe**; Montenegro is the **only** real victim.

## Extractor fix (DONE, in `data_preprocess_html.py`) — additive, no regressions

Two surgical changes, both gated so they only fire where the old code produced
nothing:

1. `_find_staff_report_html`: when no article carries an appraisal heading, **fall
   back** to the article whose `articleBody` has the most numbered narrative
   paragraphs (≥10 guard, so a title/annex-only stub is never picked).
2. `_build_sr_sections`: when no SA section exists, return **all narrative
   sections** as SR leaves (instead of `[]`), so the staff/authority split still
   runs; SA is simply empty.
3. `extract_StaffAppraisal_and_Buff_html`: write the folder's results when there
   is EITHER an SA section OR non-empty SR leaves (old guard required SA).

**Validation:**
- Montenegro now extracts: **41 staff + 4 authority paragraphs** (staff blob 33k
  chars, buff blob 3k chars) → bilateral-scoreable. ✓
- Regression: 12 known-good docs on disk re-extracted — **0 regressions**; each
  still routes through the HEADING path with a real SA section (fallback NOT
  taken). A known-good doc's selection and SA detection are byte-for-byte the
  old behavior. ✓
- Deliberately NOT changed: the silent-`success` status logging (per user; a
  separate follow-up).

## Remaining: recover Montenegro's data (needs inference — pending user go-ahead)

The extractor fix alone doesn't populate the merged files — Montenegro still has
no scored row. Recovery chain (analogous to earlier patches):

1. **Extract** (no API): build Montenegro's `df_documents`-style staff/buff blobs
   + paragraphs from the fixed extractor. (Verified: staff 33k / buff 3k chars.)
2. **Topic classification** (API, batch): classify its paragraphs into sectors →
   its `document_by_type_sector` rows. Needed so per-sector inference has input.
3. **Fine-tuned inference** (API, 4 batches): monetary/fiscal × agreement/stance
   via `inference_agreement_stance.py`.
4. **Zero-shot general** (API, 1 batch): `inference_general_agreement.py` →
   `Agreement_*` + `*_Sector`.
5. **Assemble + splice**: build the core row(s) via `final_dataset_utils` logic;
   append Montenegro into `df_aiv_merged` (text), `df_paragraphs_merged`,
   `df_documents_general_merged`, and `df_fin_reg_core_merged`. Back up first.

Cost: small (1 doc, ~5 batch jobs). This is the same "prepare → confirm → batch"
flow used for the 2024 general patch.

## Status

- [x] Root-cause diagnosed & verified on disk.
- [x] Extractor fix implemented + regression-tested (0 regressions).
- [ ] Data recovery (topic + inference + splice) — **awaiting go-ahead** (hits API).

## Note on the 12 TOC-only docs (audit gap #1 — separate)

Those are a DIFFERENT problem: their article bodies were never downloaded (only
`issue_toc.html` on disk), so no extractor fix helps — they need re-scraping.
Tracked separately as audit recommendation #3.
