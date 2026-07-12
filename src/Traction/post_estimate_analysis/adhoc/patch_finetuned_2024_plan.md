# Ad-hoc patch (A): fill the fine-tuned stance/agreement columns for the 2024 docs

## Goal

After the wrong-base re-merge was corrected (2024: 40 → 121 rows), **40 of the 121
2024 docs still have no fine-tuned stance/agreement values** (`mon_stance_*`,
`fis_stance_*`, `*_gpt_ft`). This patch fills those columns.

## The decisive finding: NO inference is needed

The fine-tuned values for these 40 docs **already exist, fully assembled**, in the
previous run's final-dataset file:

```
incremental_update/05252026_update/df_fin_core_incremental.csv
```

Verified coverage there for the 40 target docs (schema is **identical** to the
merged core — same columns, no diff):

| Column | Present (of 40) |
|---|---|
| `mon_stance_current_gpt_ft_staff` | 37 |
| `mon_stance_future_gpt_ft_staff` | 37 |
| `fis_stance_near_term_gpt_ft_staff` | 40 |
| `mon_agreement_gpt_ft` | 22 |
| `fis_agreement_gpt_ft` | 37 |
| `agreement_gpt_ft` | 40 |

So this is a **data-assembly / splice patch, not an inference patch** — zero API
calls, zero cost.

### Why the data was missing (root cause, for the record)

These 40 docs were processed end-to-end in the `05252026` run (topic → step-06
fine-tuned inference → step-07b final build); the values live in that run's
`df_fin_core_incremental.csv`. They failed to reach the current merged core purely
because of the **wrong-base merge** already diagnosed: the `06_07` merge chained
onto `main_base` (no 2024 fine-tuned) instead of the `05252026` merged output.
The correct-base re-merge restored the 81 *other* 2024 docs, but these 40 sit only
in `df_fin_core_incremental` (not in `05252026`'s **merged** core either — a second,
older gap), so the re-merge alone didn't recover them. This splice closes that.

### The 3 monetary-null docs are correct, not a gap

Of the 40, three lack **monetary** results: **Italy, Togo, Chad** — all in
currency unions (Euro area / CEMAC / WAEMU) with **no Monetary Policy topic** in
their content. Their monetary-null is a legitimate "no independent monetary
policy," not a coverage gap. They have full fiscal values. Leave monetary null.

## What to patch

The fine-tuned column family in the core (everything NOT set by the V2 zero-shot
sync). Concretely, all columns that are currently null for these 40 docs and
non-null in `05252026/df_fin_core_incremental.csv`. That is the `mon_*`/`fis_*`
stance & agreement block plus the derived overalls:

- `mon_stance_current/future_gpt_ft_staff/buff` (+ `_num` variants)
- `fis_stance_near_term_gpt_ft_staff/buff` (+ `_num`)
- `mon_agreement_gpt_ft`, `fis_agreement_gpt_ft`, `mon_disagreement_areas_gpt_ft`,
  `fis_disagreement_areas_gpt_ft`
- `mon_agreement_stance_*`, `fis_agreement_stance_*` (cate1/cate2/num/label)
- `mon_agreement_general_gpt_ft`, `fis_agreement_general_gpt_ft`,
  `fis_disagreement_areas_general_gpt_ft`
- `disagree_economic`, `agreement_gpt_ft`
- `bm_date`, `publication_date` if null (metadata)

**Explicitly NOT touched:** the 7 zero-shot `agreement_gpt*` columns (governed by
the V2 sync) and `country` / `Primary Country Code` / `year` (already correct).

## Approach — coalesce-fill from the prior final file

Mirror the merge step's own `_coalesce_overlap` semantics (fill only NaN cells,
never overwrite an existing value):

1. **Backup** `df_fin_reg_core_merged.csv` →
   `df_fin_reg_core_merged.pre_ft2024.<stamp>.bak.csv`.
2. Load current merged core (1281 rows) and
   `05252026/df_fin_core_incremental.csv`.
3. Restrict the source to the **40 target ISBNs** (normalized-key match).
4. For every column common to both **except** the protected set
   (`agreement_gpt*`, identifiers), fill the core's **NaN cells only** from the
   matching prior-final row. Count cells filled; never overwrite.
5. Write back; **verify** (below).

This is idempotent (re-running fills nothing new) and cannot regress the V2 work
(those columns are excluded) or overwrite any existing fine-tuned value.

## Verification

- Row count unchanged: **1281**; unique ISBN 1281.
- 2024 `mon_stance_current_gpt_ft_staff` present: **before 81 → after 118**
  (81 + 37; Italy/Togo/Chad stay null by design).
- 2024 `fis_stance_near_term_gpt_ft_staff` present: **before 84 → after 121**.
- The 3 monetary-null docs (Italy/Togo/Chad) remain monetary-null, fiscal-filled.
- Protected columns unchanged: spot-check that all `agreement_gpt*` values for the
  40 docs are byte-identical before/after (V2 work preserved).
- Spot-check 2–3 filled docs against the prior file (e.g. Slovenia
  `9798400274732` → `mon_stance = restrictive`).

## Artifacts

| File | Purpose |
|---|---|
| `df_fin_reg_core_merged.pre_ft2024.<stamp>.bak.csv` | backup before splice |
| `patch_finetuned_2024.py` (in `adhoc/`) | the splice script (idempotent) |
| updated `df_fin_reg_core_merged.csv` | 2024 fine-tuned filled |

## Open questions

1. **Scope of columns** — fill the entire fine-tuned block from the prior file
   (my plan), or only the headline stance/agreement columns you name? (Filling the
   whole block keeps the derived columns like `agreement_gpt_ft` internally
   consistent — recommended.)
2. **Only 2024, or all years?** The same prior-final file could back-fill any
   other year that lost fine-tuned data the same way. I scoped to 2024 per your
   request; say if you want a global NaN-coalesce from the prior final file.
