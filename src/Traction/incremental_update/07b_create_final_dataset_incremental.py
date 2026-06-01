"""
Step 07b: Create final analysis dataset from incremental results.

Combines df_aiv_incremental.csv + 4 per-sector inference results +
zero-shot general agreement into document-level analysis-ready datasets.

All transformation logic lives in
`src/Traction/post_estimate_analysis/final_dataset_utils.py` — this script is
the incremental-pipeline call site for that shared module. The main-pipeline
counterpart is `src/Traction/create_final_dataset.py`.

Outputs (written to incremental dir):
  - df_fin_incremental.csv       — full dataset with text columns and
                                    policy_mix_staff / policy_mix_buff
  - df_fin_core_incremental.csv  — core subset matching df_fin_reg_core.csv schema

Usage:
    python 07b_create_final_dataset_incremental.py [--incremental-dir DIR]
                                                   [--start-year YEAR]
                                                   [--end-year YEAR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_TRACTION_DIR = _THIS_DIR.parent
if str(_TRACTION_DIR) not in sys.path:
    sys.path.insert(0, str(_TRACTION_DIR))

import config  # noqa: E402
from post_estimate_analysis.final_dataset_utils import build_final_dataset  # noqa: E402

DEFAULT_INCREMENTAL_DIR = config.output_dir / "incremental_update" / "05252026_update"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create final analysis dataset from incremental results."
    )
    parser.add_argument(
        "--incremental-dir", type=Path, default=DEFAULT_INCREMENTAL_DIR,
        help=f"Directory with incremental outputs. Default: {DEFAULT_INCREMENTAL_DIR}",
    )
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    incr_dir = args.incremental_dir.resolve()

    df_fin_full, df_fin_core = build_final_dataset(
        source_dir=incr_dir,
        aiv_filename="df_aiv_incremental.csv",
        general_agreement_filename="df_documents_general_incremental.csv",
        start_year=args.start_year,
        end_year=args.end_year,
    )

    full_path = incr_dir / "df_fin_incremental.csv"
    df_fin_full.to_csv(full_path, index=False)
    print(f"\n  Full output: {full_path}")

    core_path = incr_dir / "df_fin_core_incremental.csv"
    df_fin_core.to_csv(core_path, index=False)
    print(f"  Core output: {core_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
