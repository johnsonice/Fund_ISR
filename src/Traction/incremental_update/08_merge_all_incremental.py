"""
Step 8: Merge incremental results, chaining onto the accumulated dataset.

Merged files are written to the incremental output directory — the base files
are NEVER modified.

Base selection (`--main-dir`, default `auto`): the script CHAINS onto the latest
prior incremental run's `*_merged.csv` outputs, so each update builds on the
accumulated dataset rather than re-seeding from `main_base`. This is deliberate:
`main_base` lags the incremental runs (it lacked a year of fine-tuned 2024 data),
so merging onto it silently DROPS documents the prior run had already processed.
Auto-chain picks the most recent run OLDER than the current one that carries all
four `*_merged.csv` files; a first-ever run (no such prior) falls back to seeding
from `main_base`. See `resolve_chain_base`.

Only a curated subset is merged (the dataset-level files + general agreement +
the regression core); the four per-sector stance/agreement results are excluded.

The main-dataset baseline lives in
`/data/home/xiong/data/Fund/CSR/Tractions/output/main_base/`, refreshed by
`src/Traction/scripts/inference/run_main_base_refresh.sh` (see
`src/Traction/main_base_refresh_step.md`).

Overrides:
  --main-dir PATH     merge against an explicit base (e.g. the frozen archive at
                      `.../Traction-archieve/output/`); pair with --main-suffix.
  --main-dir main_base / --no-auto-chain
                      seed from the raw main base (the old default behavior).

Usage:
    python 08_merge_all_incremental.py [--incremental-dir DIR]
                                       [--main-dir auto|main_base|PATH]
                                       [--main-suffix SUFFIX] [--no-auto-chain]
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

# Root under which per-run incremental output directories live (e.g.
# `.../incremental_update/06_07_2026_update/`). Used to auto-discover the latest
# prior run to chain onto — see `resolve_chain_base`.
INCREMENTAL_ROOT = config.output_dir / "incremental_update"

# A prior run is only a valid chain base if it carries the full set of merged
# outputs; otherwise chaining onto it would silently drop files.
CHAIN_BASE_MARKERS = (
    "df_aiv_merged.csv",
    "df_paragraphs_merged.csv",
    "df_documents_general_merged.csv",
    "df_fin_reg_core_merged.csv",
)

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


def _coalesce_overlap(
    df_main: pd.DataFrame,
    df_incr: pd.DataFrame,
    dedup_key: str,
) -> tuple[pd.DataFrame, int]:
    """Fill NaN cells in overlapping main rows from the matching incremental row.

    Only main rows whose key also appears in the incremental file are touched,
    and only their currently-NaN cells are filled (existing main values are
    never overwritten). Returns the patched main frame and the number of cells
    filled. Keys are matched on the normalized form so int/float/str variants of
    `Print ISBN` align (see `_normalize_key_series`).
    """
    df_main = df_main.copy()
    main_norm = _normalize_key_series(df_main[dedup_key])

    # One incremental row per key (last wins, matching how the rest of the
    # pipeline dedups), indexed by normalized key for alignment.
    incr_by_key = df_incr.copy()
    incr_by_key["_norm_key"] = _normalize_key_series(incr_by_key[dedup_key])
    incr_by_key = incr_by_key.drop_duplicates(subset="_norm_key", keep="last").set_index("_norm_key")

    # An incremental frame row-aligned to df_main's index (NaN where no overlap),
    # so we can fill column-by-column. Object dtype keeps the assignment dtype-safe
    # (no FutureWarning when e.g. a bool fills into a float column); df_main is
    # re-typed by the final to_csv round-trip anyway.
    incr_aligned = incr_by_key.reindex(main_norm.values)
    incr_aligned.index = df_main.index

    common_cols = [c for c in df_main.columns if c in df_incr.columns and c != dedup_key]
    filled = 0
    for col in common_cols:
        fill_mask = df_main[col].isna() & incr_aligned[col].notna()
        n = int(fill_mask.sum())
        if n:
            df_main[col] = df_main[col].astype(object)
            df_main.loc[fill_mask, col] = incr_aligned.loc[fill_mask, col]
            filled += n
    return df_main, filled


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

    coalesced_cells = 0
    if dedup_key and dedup_key in df_main.columns and dedup_key in df_incr.columns:
        # Keep all main rows; only append incremental rows whose key is NOT in main.
        # Normalize on both sides — see _normalize_key_series for why.
        main_keys = set(_normalize_key_series(df_main[dedup_key]))
        already_in_main = _normalize_key_series(df_incr[dedup_key]).isin(main_keys)
        skipped = int(already_in_main.sum())
        df_incr_new = df_incr[~already_in_main]

        # Coalesce overlap rows: for keys present in BOTH, keep the main row but
        # fill its NaN cells from the matching incremental row. The incremental
        # run is the fresher computation; this recovers values that a stale main
        # row left blank (e.g. sentiment labels on previously mis-coded docs)
        # without overwriting any value main already has.
        df_main, coalesced_cells = _coalesce_overlap(df_main, df_incr, dedup_key)
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
        "overlap_cells_filled_from_incremental": coalesced_cells,
        "skipped_already_in_main": skipped,
        "merged_rows": len(df_merged),
    }


def _is_chain_base(d: Path) -> bool:
    """True if `d` holds the full set of *_merged.csv outputs (a valid chain base)."""
    return d.is_dir() and all((d / m).exists() for m in CHAIN_BASE_MARKERS)


def resolve_chain_base(
    incremental_dir: Path,
    root: Path = INCREMENTAL_ROOT,
    fallback_main_dir: Path = DEFAULT_MAIN_DIR,
) -> tuple[Path, str]:
    """Pick the base to merge against, and the main-suffix to read it with.

    Auto-chains onto the LATEST prior incremental run so each update builds on the
    accumulated dataset instead of re-merging onto the (2024-fine-tuned-less)
    `main_base` — the mistake that silently dropped a year of processed docs.

    "Latest prior run" = the most-recently-modified directory under `root` that
    (a) is not `incremental_dir` itself and (b) carries the full set of
    `*_merged.csv` outputs (`_is_chain_base`). Chosen by mtime, not name, because
    run-dir names don't sort chronologically (`05252026_update` vs
    `06_07_2026_update`).

    Returns `(base_dir, main_suffix)`:
      - a prior run  -> (that dir, "_merged")   [chain onto accumulated data]
      - none found   -> (fallback_main_dir, "") [first-ever run: seed from main_base]

    Vintage guard: only runs OLDER than the current one are eligible, so
    re-running an old update doesn't chain onto a newer one. A run's vintage is
    the mtime of its incremental input (`df_fin_core_incremental.csv`), which —
    unlike the `*_merged.csv` outputs — is not rewritten by re-merging.
    """
    incremental_dir = incremental_dir.resolve()
    vintage_marker = "df_fin_core_incremental.csv"

    def _vintage(d: Path) -> float:
        f = d / vintage_marker
        return f.stat().st_mtime if f.exists() else d.stat().st_mtime

    self_vintage = _vintage(incremental_dir)
    candidates = [
        d for d in root.iterdir()
        if d.resolve() != incremental_dir and d.name != "archieve" and _is_chain_base(d)
        and _vintage(d) < self_vintage
    ]
    if not candidates:
        return fallback_main_dir, ""
    latest = max(candidates, key=_vintage)
    return latest, "_merged"


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
        type=str,
        default="auto",
        help="Directory with the base datasets to merge against. Default 'auto' "
             "chains onto the latest prior incremental run (using --main-suffix "
             "_merged automatically); pass an explicit path to override, or "
             "'main_base' to seed from the main base. See --no-auto-chain.",
    )
    parser.add_argument(
        "--main-suffix",
        type=str,
        default=None,
        help="Suffix inserted before the .csv extension of each main file (e.g. "
             "'_merged' makes 'df_aiv.csv' -> 'df_aiv_merged.csv'). Use when "
             "merging against a previous incremental run's *_merged.csv outputs. "
             "In 'auto' mode this is set for you; an explicit value overrides it.",
    )
    parser.add_argument(
        "--no-auto-chain",
        action="store_true",
        help="Disable auto-chaining; use the literal --main-dir (default main_base) "
             "with no suffix unless --main-suffix is given. Escape hatch for a "
             "deliberate merge against the raw main base.",
    )
    return parser.parse_args(argv)


def _apply_main_suffix(main_name: str, suffix: str) -> str:
    """Insert suffix before the file extension. 'df_aiv.csv' + '_merged' -> 'df_aiv_merged.csv'."""
    if not suffix:
        return main_name
    if main_name.endswith(".csv"):
        return main_name[:-4] + suffix + ".csv"
    return main_name + suffix


def _resolve_base(args: argparse.Namespace, incremental_dir: Path) -> tuple[Path, str, str]:
    """Resolve (main_dir, main_suffix, mode_note) from CLI args.

    Precedence:
      1. An explicit --main-dir (anything other than the default 'auto') is honored
         verbatim; 'main_base' is a convenience alias for the configured main base.
         --main-suffix defaults to '' here unless the user set it.
      2. --no-auto-chain forces the main-base seed with no suffix (unless overridden).
      3. Otherwise 'auto': chain onto the latest prior run (suffix '_merged'), or
         fall back to main_base for the first-ever run.
    An explicit --main-suffix always wins over the auto-selected one.
    """
    explicit_dir = args.main_dir != "auto"

    if explicit_dir:
        main_dir = (DEFAULT_MAIN_DIR if args.main_dir == "main_base" else Path(args.main_dir)).resolve()
        suffix = args.main_suffix or ""
        note = f"explicit --main-dir ({main_dir.name})"
    elif args.no_auto_chain:
        main_dir = DEFAULT_MAIN_DIR.resolve()
        suffix = args.main_suffix or ""
        note = "auto-chain disabled -> main_base seed"
    else:
        base, auto_suffix = resolve_chain_base(incremental_dir)
        main_dir = base.resolve()
        suffix = args.main_suffix if args.main_suffix is not None else auto_suffix
        if main_dir == DEFAULT_MAIN_DIR.resolve():
            note = "auto: no prior run found -> main_base seed (first run)"
        else:
            note = f"auto: chaining onto latest prior run '{main_dir.name}'"
    return main_dir, suffix, note


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    incremental_dir = args.incremental_dir.resolve()
    main_dir, main_suffix, mode_note = _resolve_base(args, incremental_dir)

    print(f"Incremental dir: {incremental_dir}")
    print(f"Main dir:        {main_dir}  [{mode_note}]")
    if main_suffix:
        print(f"Main suffix:     {main_suffix} (reading e.g. df_aiv{main_suffix}.csv from main dir)")
    print(f"Merged outputs:  {incremental_dir}")
    print()

    for incr_name, main_name, merged_name, dedup_key in MERGE_SPECS:
        incr_path = incremental_dir / incr_name
        main_path = main_dir / _apply_main_suffix(main_name, main_suffix)
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
