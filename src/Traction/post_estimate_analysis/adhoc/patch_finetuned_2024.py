"""Ad-hoc patch: fill the fine-tuned stance/agreement columns for 2024 docs.

The 2024 docs that still lack fine-tuned values (`mon_stance_*`, `fis_stance_*`,
`*_gpt_ft`, ...) already have those values fully assembled in the previous run's
final-dataset file:

    incremental_update/05252026_update/df_fin_core_incremental.csv

(identical schema to the merged core). They never reached the current merged core
because of the wrong-base merge chain — this splices them back in. NO inference.

Semantics (mirrors step-08 `_coalesce_overlap`): for the target 2024 ISBNs, fill
ONLY currently-NaN cells in the merged core from the matching prior-final row;
never overwrite an existing value. The zero-shot `agreement_gpt*` columns (owned
by the V2 sync) and identifiers are PROTECTED — never touched. Idempotent.

Usage:
    python patch_finetuned_2024.py            # apply
    python patch_finetuned_2024.py --dry-run  # report what would change, write nothing
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import pandas as pd

OUTPUT_ROOT = Path("/data/home/xiong/data/Fund/CSR/Tractions/output")
CORE = OUTPUT_ROOT / "incremental_update" / "06_07_2026_update" / "df_fin_reg_core_merged.csv"
PRIOR_FINAL = OUTPUT_ROOT / "incremental_update" / "05252026_update" / "df_fin_core_incremental.csv"

# Columns owned by the V2 zero-shot sync + identifiers — never fill these here.
PROTECTED = {
    "Print ISBN", "country", "Primary Country Code", "year",
    "agreement_gpt", "agreement_gpt_Monetary", "agreement_gpt_Fiscal",
    "agreement_gpt_External", "agreement_gpt_Financial", "agreement_gpt_Real",
    "agreement_gpt_Other",
}

TARGET_YEAR = 2024


def _norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.replace(r"\.0$", "", regex=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="report changes, write nothing")
    args = ap.parse_args()

    core = pd.read_csv(CORE, low_memory=False)
    prior = pd.read_csv(PRIOR_FINAL, low_memory=False)
    core["_k"] = _norm(core["Print ISBN"])
    prior["_k"] = _norm(prior["Print ISBN"])

    # Target = 2024 docs currently missing fine-tuned monetary AND/OR fiscal stance.
    c24 = core[core["year"] == TARGET_YEAR]
    need_mask = c24["mon_stance_current_gpt_ft_staff"].isna() | c24["fis_stance_near_term_gpt_ft_staff"].isna()
    targets = set(c24.loc[need_mask, "_k"])
    print(f"2024 docs needing fine-tuned fill: {len(targets)}")

    prior_by_k = prior.drop_duplicates("_k", keep="last").set_index("_k")
    missing_in_prior = targets - set(prior_by_k.index)
    if missing_in_prior:
        print(f"  WARNING: {len(missing_in_prior)} target docs absent from prior final file: {sorted(missing_in_prior)}")
    targets &= set(prior_by_k.index)

    # Snapshot protected columns to prove they are untouched.
    protected_cols = [c for c in core.columns if c in PROTECTED]
    before_protected = core.loc[core["_k"].isin(targets), protected_cols].copy()

    fillable = [c for c in core.columns if c in prior.columns and c not in PROTECTED and c != "_k"]

    # Row-align the prior rows to the target core rows.
    tgt_idx = core.index[core["_k"].isin(targets)]
    aligned = prior_by_k.reindex(core.loc[tgt_idx, "_k"].values)
    aligned.index = tgt_idx

    filled_cells = 0
    per_col = {}
    for col in fillable:
        core_sub = core.loc[tgt_idx, col]
        src = aligned[col]
        fill_mask = core_sub.isna() & src.notna()
        n = int(fill_mask.sum())
        if n:
            if not args.dry_run:
                core[col] = core[col].astype(object)
                core.loc[fill_mask[fill_mask].index, col] = src[fill_mask].values
            filled_cells += n
            per_col[col] = n

    print(f"\ncells to fill: {filled_cells} across {len(per_col)} columns")
    for c, n in sorted(per_col.items(), key=lambda x: -x[1])[:20]:
        print(f"  {c:44} {n}")

    # Protected-column integrity check
    after_protected = core.loc[core["_k"].isin(targets), protected_cols]
    same = before_protected.reset_index(drop=True).equals(after_protected.reset_index(drop=True))
    print(f"\nprotected (agreement_gpt*/ids) unchanged for targets: {same}")
    assert same, "protected columns changed — aborting"

    # Coverage after
    c24b = core[core["year"] == TARGET_YEAR]
    print("\n2024 fine-tuned coverage after fill:")
    for c in ["mon_stance_current_gpt_ft_staff", "fis_stance_near_term_gpt_ft_staff",
              "mon_agreement_gpt_ft", "fis_agreement_gpt_ft", "agreement_gpt_ft"]:
        print(f"  {c:38}: {c24b[c].notna().sum()}/{len(c24b)}")

    if args.dry_run:
        print("\n[dry-run] nothing written.")
        return

    stamp = pd.Timestamp("now").strftime("%Y%m%d_%H%M%S")  # note: local ts for backup name
    backup = CORE.with_name(f"{CORE.stem}.pre_ft2024.{stamp}.bak.csv")
    shutil.copy2(CORE, backup)
    print(f"\nbacked up -> {backup.name}")

    core.drop(columns=["_k"]).to_csv(CORE, index=False)
    print(f"wrote {CORE} ({len(core)} rows)")


if __name__ == "__main__":
    main()
