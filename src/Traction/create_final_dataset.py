"""
Build the main-pipeline final analysis dataset.

Combines df_aiv.csv + 4 per-sector inference results + zero-shot general
agreement into document-level analysis-ready datasets. This is the
main-pipeline counterpart of
`src/Traction/incremental_update/07b_create_final_dataset_incremental.py`;
both call the same logic in
`src/Traction/post_estimate_analysis/final_dataset_utils.py`.

Outputs (written to --source-dir):
  - df_fin.csv          — full dataset with text columns and
                           policy_mix_staff / policy_mix_buff
  - df_fin_reg_core.csv — core subset matching the archive's
                           df_fin_reg_core.csv schema (consumed by
                           incremental_update/08_merge_all_incremental.py)

Usage:
    python create_final_dataset.py [--source-dir DIR]
                                   [--start-year YEAR]
                                   [--end-year YEAR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import config  # noqa: E402
from post_estimate_analysis.final_dataset_utils import build_final_dataset  # noqa: E402

DEFAULT_SOURCE_DIR = config.output_dir / "main_base"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create main-pipeline final analysis dataset from inference outputs."
    )
    parser.add_argument(
        "--source-dir", type=Path, default=DEFAULT_SOURCE_DIR,
        help=f"Directory with main-pipeline outputs. Default: {DEFAULT_SOURCE_DIR}",
    )
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    src_dir = args.source_dir.resolve()

    df_fin_full, df_fin_core = build_final_dataset(
        source_dir=src_dir,
        aiv_filename="df_aiv.csv",
        general_agreement_filename="df_documents_general.csv",
        start_year=args.start_year,
        end_year=args.end_year,
    )

    full_path = src_dir / "df_fin.csv"
    df_fin_full.to_csv(full_path, index=False)
    print(f"\n  Full output: {full_path}")

    core_path = src_dir / "df_fin_reg_core.csv"
    df_fin_core.to_csv(core_path, index=False)
    print(f"  Core output: {core_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
