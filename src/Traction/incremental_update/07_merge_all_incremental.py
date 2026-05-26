"""
Step 7: Merge all incremental results with main datasets.

Merged files are written to the incremental output directory — the original
main files are NEVER modified.

Usage:
    python 07_merge_all_incremental.py [--incremental-dir DIR] [--main-dir DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_THIS_DIR = Path(__file__).resolve().parent
_TRACTION_DIR = _THIS_DIR.parent
if str(_TRACTION_DIR) not in sys.path:
    sys.path.insert(0, str(_TRACTION_DIR))

import config  # noqa: E402

DEFAULT_INCREMENTAL_DIR = config.output_dir / "incremental_update" / "05252026_update"
DEFAULT_MAIN_DIR = config.output_dir

# Normalize incremental topic names to match the main dataset's short convention.
TOPIC_RENAME = {
    "Economic Outlook": "Real",
    "Monetary Policy": "Monetary",
    "Fiscal Stance": "Fiscal",
    "Financial Stability": "Financial",
    "External Stance": "External",
}

# Files to merge: (incremental_name, main_name, merged_output_name, dedup_key)
# dedup_key is used to identify rows already in main — only genuinely new rows are appended.
MERGE_SPECS = [
    ("df_aiv_incremental.csv",                "df_aiv.csv",                    "df_aiv_merged.csv",                    "Print ISBN"),
    ("df_paragraphs_incremental.csv",         "df_paragraphs.csv",            "df_paragraphs_merged.csv",             "Print ISBN"),
    ("document_by_type_sector_incremental.csv","document_by_type_sector.csv",  "document_by_type_sector_merged.csv",   "Print ISBN"),
    ("agreement_monetary_results.csv",         "agreement_monetary_results.csv","agreement_monetary_results_merged.csv", "Print ISBN"),
    ("agreement_fiscal_results.csv",           "agreement_fiscal_results.csv",  "agreement_fiscal_results_merged.csv",  "Print ISBN"),
    ("stance_monetary_results.csv",            "stance_monetary_results.csv",   "stance_monetary_results_merged.csv",   "Print ISBN"),
    ("stance_fiscal_results.csv",              "stance_fiscal_results.csv",     "stance_fiscal_results_merged.csv",     "Print ISBN"),
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
        # Keep all main rows; only append incremental rows whose key is NOT in main
        main_keys = set(df_main[dedup_key].astype(str))
        already_in_main = df_incr[dedup_key].astype(str).isin(main_keys)
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
