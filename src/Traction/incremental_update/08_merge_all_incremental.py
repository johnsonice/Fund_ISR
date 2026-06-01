"""
Step 8: Merge incremental results against the main-pipeline base.

Merged files are written to the incremental output directory — the main-base
files are NEVER modified.

The main-dataset baseline lives in
`/data/home/xiong/data/Fund/CSR/Tractions/output/main_base/`, refreshed by
`src/Traction/scripts/inference/run_main_base_refresh.sh` (see
`src/Traction/main_base_refresh_step.md`). We merge a curated subset of the
incremental outputs against it (not the four per-sector stance/agreement
results — those are intentionally excluded; only the dataset-level files and
the new general-agreement output are folded in).

To merge against a different base (e.g. the frozen archive at
`/data/home/xiong/data/Fund/CSR/Traction-archieve/output/`), pass
`--main-dir` explicitly.

Usage:
    python 08_merge_all_incremental.py [--incremental-dir DIR] [--main-dir DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


def _normalize_key_series(s: pd.Series) -> pd.Series:
    """Normalize a dedup-key column so int/float/string variants compare equal.

    `Print ISBN` ends up as float64 in some archive CSVs (pandas infers float
    when any row is NaN) and int64 in incremental CSVs. A naive `.astype(str)`
    then yields '9798400259814.0' vs '9798400259814', breaking the overlap
    check. Strip trailing '.0' after string-casting to fix this.
    """
    return s.astype(str).str.replace(r'\.0$', '', regex=True)


_THIS_DIR = Path(__file__).resolve().parent
_TRACTION_DIR = _THIS_DIR.parent
if str(_TRACTION_DIR) not in sys.path:
    sys.path.insert(0, str(_TRACTION_DIR))

import config  # noqa: E402

DEFAULT_INCREMENTAL_DIR = config.output_dir / "incremental_update" / "05252026_update"
DEFAULT_MAIN_DIR = config.output_dir / "main_base"

# Normalize incremental topic names to match the main dataset's short convention.
TOPIC_RENAME = {
    "Economic Outlook": "Real",
    "Monetary Policy": "Monetary",
    "Fiscal Stance": "Fiscal",
    "Financial Stability": "Financial",
    "External Stance": "External",
}

# Files to merge: (incremental_name, main_name_relative_to_main_dir, merged_output_name, dedup_key)
# dedup_key identifies rows already in main — only genuinely new rows are appended.
# Per user direction: only merge the dataset-level files + general agreement +
# the regression core. Per-task stance/agreement results (monetary/fiscal ×
# stance/agreement) are intentionally NOT merged here.
#
# Note: `document_by_type_sector_incremental.csv` is intentionally NOT merged.
# It has a different schema from the archive's `df_documents_sector.csv` (long
# format with type/topic/text vs wide doc-level with 73 cols of metadata), so
# concat would produce an incoherent table. Both files remain available
# separately in their respective directories.
MERGE_SPECS = [
    ("df_aiv_incremental.csv",                "df_aiv.csv",                    "df_aiv_merged.csv",                    "Print ISBN"),
    ("df_paragraphs_incremental.csv",         "df_paragraphs.csv",             "df_paragraphs_merged.csv",             "Print ISBN"),
    ("df_documents_general_incremental.csv",  "df_documents_general.csv",      "df_documents_general_merged.csv",      "Print ISBN"),
    ("df_fin_core_incremental.csv",           "df_fin_reg_core.csv",           "df_fin_reg_core_merged.csv",           "Print ISBN"),
]


def _merge_one(
    incremental_path: Path,
    main_path: Path,
    output_path: Path,
    dedup_key: str | None,
) -> dict:
    """Merge one pair of files. Returns summary stats."""
    if not incremental_path.exists():
        return {"status": "skipped", "reason": f"incremental file not found: {incremental_path.name}"}

    df_incr = pd.read_csv(incremental_path)
    incr_rows = len(df_incr)

    if not main_path.exists():
        # No main file — just copy incremental as the merged output
        df_incr.to_csv(output_path, index=False)
        return {
            "status": "created",
            "incremental_rows": incr_rows,
            "main_rows": 0,
            "merged_rows": incr_rows,
        }

    df_main = pd.read_csv(main_path)
    main_rows = len(df_main)

    if dedup_key and dedup_key in df_main.columns and dedup_key in df_incr.columns:
        # Keep all main rows; only append incremental rows whose key is NOT in main.
        # Normalize on both sides — see _normalize_key_series for why.
        main_keys = set(_normalize_key_series(df_main[dedup_key]))
        already_in_main = _normalize_key_series(df_incr[dedup_key]).isin(main_keys)
        skipped = int(already_in_main.sum())
        df_incr_new = df_incr[~already_in_main]
    else:
        skipped = 0
        df_incr_new = df_incr

    new_rows = len(df_incr_new)
    df_merged = pd.concat([df_main, df_incr_new], ignore_index=True)

    # Normalize topic names so incremental values match main convention
    if "topic" in df_merged.columns:
        df_merged["topic"] = df_merged["topic"].replace(TOPIC_RENAME)

    df_merged.to_csv(output_path, index=False)

    return {
        "status": "merged",
        "main_rows": main_rows,
        "incremental_rows": incr_rows,
        "new_rows_added": new_rows,
        "skipped_already_in_main": skipped,
        "merged_rows": len(df_merged),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge incremental results with main datasets.")
    parser.add_argument(
        "--incremental-dir",
        type=Path,
        default=DEFAULT_INCREMENTAL_DIR,
        help=f"Directory with incremental outputs. Default: {DEFAULT_INCREMENTAL_DIR}",
    )
    parser.add_argument(
        "--main-dir",
        type=Path,
        default=DEFAULT_MAIN_DIR,
        help=f"Directory with main datasets. Default: {DEFAULT_MAIN_DIR}",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    incremental_dir = args.incremental_dir.resolve()
    main_dir = args.main_dir.resolve()

    print(f"Incremental dir: {incremental_dir}")
    print(f"Main dir:        {main_dir}")
    print(f"Merged outputs:  {incremental_dir}")
    print()

    for incr_name, main_name, merged_name, dedup_key in MERGE_SPECS:
        incr_path = incremental_dir / incr_name
        main_path = main_dir / main_name
        output_path = incremental_dir / merged_name

        result = _merge_one(incr_path, main_path, output_path, dedup_key)
        status = result.pop("status")

        print(f"  {merged_name}: {status}")
        for k, v in result.items():
            print(f"    {k}: {v}")

    print("\nDone. All merged files are in:", incremental_dir)
    print("Original files in", main_dir, "are untouched.")


if __name__ == "__main__":
    main()
