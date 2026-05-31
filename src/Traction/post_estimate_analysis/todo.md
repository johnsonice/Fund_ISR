# Country metadata fixes — TODO

Tracked from `results_data_transformation.ipynb` merge of `df_aiv.csv` with `docs/reference/country_meta_info.xlsx`.

**Problem:** 8 distinct `Primary Country Code` values (plus 165 `NaN` rows) fail the merge on `ISO3`, so `Country`, `Income`, and derived `income_group` are missing.

**Reference:** `src/Traction/docs/reference/country_meta_info.xlsx` (192 countries; Kosovo = `KOS`)

**Source data:** `/data/home/xiong/data/Fund/CSR/Tractions/output/df_aiv.csv`

---

## 1. Code remapping (IMF → reference ISO3)

Apply before merging with `country_meta_info.xlsx` (notebook, `data_preprocess.py`, or upstream metadata QA).

| IMF / source code | Maps to | Entity | Doc count (approx.) |
|-------------------|---------|--------|---------------------|
| `UVK` | `KOS` | Republic of Kosovo | 6 |
| `CEE` | `SVN` | Republic of Slovenia (metadata typo) | 1 |
| `ABW` | *(see §2)* | Aruba | 5 |
| `CUW` | *(see §2)* | Curaçao (+ Sint Maarten joint reports) | 5 |
| `MAC` | *(see §2)* | Macao SAR | 4 |
| `ANT` | `CUW` or split | Netherlands Antilles (obsolete; 2016 joint report) | 1 |

- [ ] Add explicit remap dict (e.g. in `data_vis_utils.py` or shared config) and use in notebook + pipeline
- [ ] Align with `incremental_update_step.md`: Kosovo must be `KOS`, not `UVK`

---

## 2. Extend `country_meta_info.xlsx`

These territories appear in Article IV titles but are **not** in the reference workbook today.

| Proposed ISO3 | Country name | Suggested income | Notes |
|---------------|--------------|------------------|-------|
| `ABW` | Aruba | TBD | Kingdom of the Netherlands |
| `CUW` | Curaçao | TBD | Joint consultations with Sint Maarten |
| `MAC` | Macao SAR | TBD | Distinct from `CHN` (mainland) |
| `SXM` | Sint Maarten | TBD | If split from joint `CUW` reports |

- [ ] Decide income group (`AE` / `EM` / `LC`) per IMF WEO or internal convention
- [ ] Add rows to `country_meta_info.xlsx` with UN/IMF region columns filled consistently
- [ ] Re-run merge QA: zero rows with missing `Income` for territory codes above

---

## 3. Regional / non-country consultations (do not treat as countries)

| Code | Entity | Doc count | Action |
|------|--------|-----------|--------|
| `EUR` | Euro Area Policies | 3 | Flag `document_type = regional`; exclude from country-level stats or map to member list |
| *(NaN title)* | Eastern Caribbean Currency Union | 2+ | Same treatment; assign ECCU code or exclude |
| *(NaN title)* | Euro Area (2021, 2023) | 2+ | Same as `EUR` |

- [ ] Define handling in `results_data_transformation.ipynb` (filter vs. separate analysis bucket)
- [ ] Document in final dataset schema (`df_fin.csv` column glossary)

---

## 4. Rows with missing `Primary Country Code` (165 rows)

Many have empty `Title`; some have titles but no code (e.g. Croatia, Zambia, Equatorial Guinea, Euro Area, ECCU).

- [ ] Trace back to source metadata workbook used by `data_preprocess.py`
- [ ] Fill `Primary Country Code` + `Primary Country Description` from title via `02_meta_data_postprocess.py` logic
- [ ] Manual QA for ambiguous / multi-country titles
- [ ] Drop or exclude rows that remain without code after QA (if not valid AIV country reports)

---

## 5. Notebook / analysis pipeline

File: `post_estimate_analysis/results_data_transformation.ipynb`

- [ ] Apply code remap before `merge(country_map, ...)`
- [ ] Re-check `missing_codes_df` cell until empty (or only intentional regional docs)
- [ ] Use `dv.classify_income_group_from_code()` only after codes are normalized
- [ ] Log/count excluded regional and failed-QA rows in final output

---

## 6. Upstream metadata QA (prevent recurrence)

Files: metadata postprocess + incremental update (`02_meta_data_postprocess.py`, `03_incremental_aiv_update.py`, `incremental_update_step.md`)

- [ ] Validate all new rows against `country_meta_info.xlsx` before export to `df_aiv.csv`
- [ ] Fail or warn on codes not in reference (except approved regional list)
- [ ] Fix Slovenia source metadata so `CEE` is never written (should be `SVN`)

---

## 7. Verification checklist

After changes:

- [ ] `df_aiv` merge: no unexpected `Income.isna()` for standard country AIVs (2015–2023 sample)
- [ ] Kosovo rows: `Primary Country Code == KOS`, country name matches reference
- [ ] Aruba / Curaçao / Macao: income group populated
- [ ] Euro Area / ECCU: explicitly tagged or excluded, not silently dropped
- [ ] Re-export `df_fin.csv` and spot-check country-level charts/tables

---

## Summary counts (baseline)

| `Primary Country Code` | Rows |
|------------------------|------|
| `NaN` | 165 |
| `UVK` | 6 |
| `ABW` | 5 |
| `CUW` | 5 |
| `MAC` | 4 |
| `EUR` | 3 |
| `ANT` | 1 |
| `CEE` | 1 |
