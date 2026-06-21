# `df_fin_reg_core.csv` — Variable Definitions

One row per Article IV document (keyed by `Print ISBN`). This file is the
"core" analysis-ready dataset built by
[`final_dataset_utils.build_final_dataset`](../post_estimate_analysis/final_dataset_utils.py),
called by `create_final_dataset.py` (main) and
`incremental_update/07b_create_final_dataset_incremental.py` (incremental).
The merged variant `df_fin_reg_core_merged.csv` is the same schema with the
incremental run row-appended/coalesced onto the main base by
`incremental_update/08_merge_all_incremental.py`.

## Inputs and how they combine

| Input file | Provides | Joined on |
|---|---|---|
| `df_aiv*.csv` | document metadata + extracted text | base table |
| `country_meta_info.xlsx` | `country`, income group | `Primary Country Code → ISO3` (left) |
| `agreement_monetary_results.csv` | monetary agreement (fine-tuned model) | `Print ISBN` (left) |
| `agreement_fiscal_results.csv` | fiscal agreement (fine-tuned model) | `Print ISBN` (left) |
| `stance_monetary_results.csv` | monetary stance, staff & authority (fine-tuned) | `Print ISBN` (left, pivoted wide) |
| `stance_fiscal_results.csv` | fiscal stance, staff & authority (fine-tuned) | `Print ISBN` (left, pivoted wide) |
| `df_documents_general*.csv` | zero-shot cross-sector agreement scores | `Print ISBN` (left) |

"staff" = IMF staff view; "buff" = country authorities' view (Buff statement /
Authorities' Views). All `*_gpt_ft` columns come from **fine-tuned GPT‑4.1**
models; all `agreement_gpt*` columns come from **zero-shot** general
classification.

## Missing-value convention (read this first)

A blank cell almost never means "pipeline lost data." There are three distinct
reasons a sentiment cell is blank, and they are **not currently distinguishable**
in this file (they all become NaN):

1. **Not applicable** — the document has no discussion of that sector (e.g.
   monetary policy for Euro‑area members, ECCU/dollarized economies). The doc was
   never sent to that sector's model, so it is absent from the results file →
   left join yields NaN.
2. **`irrelevant` / `unclear`** — the model *did* score it but judged there is no
   stance/agreement to compare. Converted to NaN at the binarize step
   (see [final_dataset_utils.py:574-581](../post_estimate_analysis/final_dataset_utils.py#L574-L581))
   because the numeric agreement columns are forced to a 0/1 scale on which
   "irrelevant" has no place.

NaN is used (not `0`) so that means/rates computed with `.mean()` automatically
exclude undefined documents rather than miscounting `irrelevant` as
"disagreement."

---

## Identifier & metadata columns

| Column | Type | Definition / calculation |
|---|---|---|
| `Print ISBN` | str | Document primary key. Package-folder identifier carried from step 01/03. Dedup key for the merge. |
| `country` | str | Country name. From `Primary Country Description` (incremental) or the reference `Country` joined on ISO3 (main). |
| `Primary Country Code` | str | ISO3 country code. Title-derived in step 02; legacy/non-standard codes normalized via [`country_aliases.py`](../country_aliases.py) (e.g. `UVK→KOS`, `EUR→G163`) before the reference join. |
| `year` | int | `Year from title` (publication year fallback). Docs with no parseable year are dropped upstream. |
| `publication_date` | str | Publication date from metadata. |
| `bm_date` | float | Benchmark date placeholder; initialized NaN (reserved, not populated here). |

---

## Zero-shot general agreement (`agreement_gpt*`)

Cross-sector agreement scores from the **zero-shot** general classifier
(`df_documents_general*.csv`), merged on `Print ISBN`. Score scale is roughly
**−5 … +5** (signed agreement intensity; higher = more agreement). The sentinel
value `99` is mapped to NaN
([final_dataset_utils.py:538-539](../post_estimate_analysis/final_dataset_utils.py#L538-L539)).

| Column | Type | Definition |
|---|---|---|
| `agreement_gpt` | float (−5..5) | Overall (general) staff–authority agreement. |
| `agreement_gpt_Monetary` | float (−5..5) | Agreement on Monetary sector. |
| `agreement_gpt_Fiscal` | float (−5..5) | Agreement on Fiscal sector. |
| `agreement_gpt_External` | float (−5..5) | Agreement on External sector. |
| `agreement_gpt_Financial` | float (−5..5) | Agreement on Financial sector. |
| `agreement_gpt_Real` | float (−5..5) | Agreement on Real/economic-outlook sector. |
| `agreement_gpt_Other` | float (−5..5) | Agreement on Other (v2 prompt only; NaN under legacy v1). |

---

## Monetary — fine-tuned stance & agreement

### Raw stance labels (categorical)
Pivoted from `stance_monetary_results.csv` to one staff and one buff column each
([final_dataset_utils.py:446-455](../post_estimate_analysis/final_dataset_utils.py#L446-L455)).
`moderately tight`/`tightening bias` are folded into `restrictive`, `close to
neutral` into `neutral`.

| Column | Type | Values |
|---|---|---|
| `mon_stance_current_gpt_ft_staff` | str | Staff's *current* monetary stance: `accommodative` / `neutral` / `restrictive` (+ `unclear`/`irrelevant`). |
| `mon_stance_current_gpt_ft_buff` | str | Authorities' current monetary stance (same scale). |
| `mon_stance_future_gpt_ft_staff` | str | Staff's *future* monetary direction: `tightening` / `tightening bias` / `no change` / `loosening bias` / `loosening`. |
| `mon_stance_future_gpt_ft_buff` | str | Authorities' future monetary direction (same scale). |

### Numeric stance encodings
- Current: `accommodative=0, neutral=1, restrictive=2` (`STANCE_CURRENT_DICT`).
- Future: `loosening=1, loosening bias=2, no change=3, tightening bias=4, tightening=5` (`STANCE_FUTURE_DICT`).

| Column | Type | Calculation |
|---|---|---|
| `mon_stance_current_gpt_ft_staff_num` | float 0–2 | `map(STANCE_CURRENT_DICT)` of staff current. |
| `mon_stance_current_gpt_ft_buff_num` | float 0–2 | Authorities current, numeric. |
| `mon_stance_future_gpt_ft_staff_num` | float 1–5 | `map(STANCE_FUTURE_DICT)` of staff future. |
| `mon_stance_future_gpt_ft_buff_num` | float 1–5 | Authorities future, numeric. |
| `mon_agreement_stance_current_gpt_ft_num` | float | staff_num − buff_num (current). >0 = staff more restrictive. |
| `mon_agreement_stance_future_gpt_ft_num` | float | staff_num − buff_num (future). >0 = staff more hawkish. |

### Stance-difference categories
From the `_num` differences ([final_dataset_utils.py:203-225](../post_estimate_analysis/final_dataset_utils.py#L203-L225)):

| Column | Type | Calculation |
|---|---|---|
| `mon_agreement_stance_future_gpt_ft_cate1` | str | Magnitude of future gap: `no difference` (0) / `minor` (1) / `some` (2) / `major difference` (≥3); `irrelevant` if undefined. |
| `mon_agreement_stance_future_gpt_ft_cate2` | str | Signed future gap: `same`(0) → `moderately/…/significantly tighter` (staff>auth) or `looser` (staff<auth). |
| `mon_agreement_stance_current_gpt_ft_cate2` | str | Signed current gap: `same` / `more restrictive` (staff>auth) / `more accommodative` (staff<auth). |

### Agreement labels (string) and the binary `_gpt_ft`
| Column | Type | Calculation |
|---|---|---|
| `mon_agreement_stance_current_gpt_ft` | str | `irrelevant` if either side unclear/irrelevant; else `mostly agree` if staff==buff current stance, else `disagreement exists`. |
| `mon_agreement_stance_future_gpt_ft` | str | `irrelevant` if either side unclear; else `mostly agree` if `|future gap| ≤ 1`, else `disagreement exists`. |
| `mon_agreement_gpt_ft` | float {0,1} | **Text-based** monetary agreement from `agreement_monetary_results.csv`. Binarized: `mostly agree→1`, `disagreement exists→0`, `irrelevant→NaN`. |
| `mon_disagreement_areas_gpt_ft` | list(str) | Free-text disagreement topics from the monetary agreement model (lowercased list; `[]` if none). |
| `mon_agreement_general_gpt_ft` | float {0,1} | Combined monetary agreement (`_mon_general_agree`, [L291-309](../post_estimate_analysis/final_dataset_utils.py#L291-L309)): `irrelevant`→NaN if current+future stance and text all irrelevant; else `disagreement exists`(0) if current-stance disagreement, or future gap `>1`, or text disagreement (outside "Future Policy Direction"); else `mostly agree`(1). |

---

## Fiscal — fine-tuned stance & agreement

Fiscal stance is a single **near-term** direction (no separate current/future).
Pivoted from `stance_fiscal_results.csv`; numeric uses the same
`STANCE_FUTURE_DICT` (1–5) scale.

| Column | Type | Calculation |
|---|---|---|
| `fis_stance_near_term_gpt_ft_staff` | str | Staff near-term fiscal direction: `tightening`…`loosening`. |
| `fis_stance_near_term_gpt_ft_buff` | str | Authorities near-term fiscal direction. |
| `fis_stance_near_term_gpt_ft_staff_num` | float 1–5 | Staff, numeric (`STANCE_FUTURE_DICT`). |
| `fis_stance_near_term_gpt_ft_buff_num` | float 1–5 | Authorities, numeric. |
| `fis_agreement_stance_near_term_gpt_ft_num` | float | staff_num − buff_num. >0 = staff tighter. |
| `fis_agreement_stance_near_term_gpt_ft_cate1` | str | Magnitude of gap: `no`/`minor`/`some`/`major difference`. |
| `fis_agreement_stance_near_term_gpt_ft_cate2` | str | Signed gap: `same` → tighter/looser bands. |
| `fis_agreement_stance_near_term_gpt_ft` | str | `irrelevant` if either side unclear; else `mostly agree` if `|gap|≤1`, else `disagreement exists`. |
| `fis_agreement_gpt_ft` | float {0,1} | **Text-based** fiscal agreement from `agreement_fiscal_results.csv`, binarized (`mostly agree→1`, `disagreement exists→0`, `irrelevant→NaN`). Hallucinated label variants are cleaned to `mostly agree`. |
| `fis_disagreement_areas_gpt_ft` | list(str) | Free-text fiscal disagreement topics (lowercased list). |
| `fis_agreement_general_gpt_ft` | float {0,1} | Combined fiscal agreement (`_fis_general_agree`, [L312-326](../post_estimate_analysis/final_dataset_utils.py#L312-L326)): `irrelevant`→NaN if near-term stance and text both irrelevant; else `disagreement exists`(0) if `|gap|>1` or text disagreement (outside near-term direction); else `mostly agree`(1). |
| `fis_disagreement_areas_general_gpt_ft` | list(str) | `fis_disagreement_areas` plus `"near-term policy direction"` appended when the stance-based agreement found a near-term disagreement. |

---

## Overall / derived

| Column | Type | Calculation |
|---|---|---|
| `disagree_economic` | bool | True if `"economic assessment"` appears in either `mon_` or `fis_disagreement_areas_gpt_ft` ([L584-588](../post_estimate_analysis/final_dataset_utils.py#L584-L588)). |
| `agreement_gpt_ft` | bool | Overall staff–authority agreement across sectors ([L590-594](../post_estimate_analysis/final_dataset_utils.py#L590-L594)): True if both `mon_agreement_general_gpt_ft` and `fis_agreement_general_gpt_ft` == 1, **or** one is NaN and the other == 1. |

---

## Quick value-scale cheat sheet

- **Binary agreement** (`*_agreement_gpt_ft`, `*_agreement_general_gpt_ft`):
  `1 = mostly agree`, `0 = disagreement exists`, `NaN = irrelevant/not applicable`.
- **Stance current** numeric: `0 accommodative · 1 neutral · 2 restrictive`.
- **Stance future / fiscal near-term** numeric: `1 loosening · 2 loosening bias · 3 no change · 4 tightening bias · 5 tightening`.
- **Stance gap `_num`** = staff − authority (positive ⇒ staff tighter/more hawkish).
- **Zero-shot `agreement_gpt*`**: signed scale ≈ −5…+5 (higher ⇒ more agreement); `99`→NaN.
- **`*_areas*`**: Python-list-as-string of lowercased free-text topics; `[]` when none.

## Authoritative source

All definitions above are implemented in
[`post_estimate_analysis/final_dataset_utils.py`](../post_estimate_analysis/final_dataset_utils.py).
For the encoding dicts see `STANCE_CURRENT_DICT` / `STANCE_FUTURE_DICT`; for the
column rename to the legacy `_gpt_ft` schema see `RENAME_MAP`; for the final
column set see `CORE_COLUMNS`.
