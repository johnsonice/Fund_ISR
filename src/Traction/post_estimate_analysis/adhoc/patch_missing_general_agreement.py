"""Ad-hoc patch: score the general-agreement gap docs and append to df_documents_general_v2.csv.

Background
----------
`df_documents_general_v2.csv` (the zero-shot general-agreement output, v2 schema)
covers 981 docs. The analysis-ready core (`df_fin_reg_core_merged.csv`) covers 38
more — a set of 2024 Article IV reports (plus one 2017 CEMAC doc) that the
general-agreement step never ran on, because that step was last executed on a
pre-2024 981-doc snapshot while the doc backbone was later refreshed.

This script prepares the top-up input WITHOUT re-running topic classification or
the full corpus. The general-agreement step needs no topic labels: it reads
doc-level staff/buff text and the model emits both the Agreement_* scores and the
*_Sector lists in one call.

Phases
------
  build-input : assemble the missing docs' staff/buff text into an input CSV and
                write an excluded-docs report. (Run this now — no API calls.)
  append      : after the batch inference has produced the patch results CSV,
                concat it into df_documents_general_v2.csv (idempotent). (Run later.)

The inference itself is a SEPARATE manual step between the two phases:

  python inference_general_agreement.py \
    --data-file  <ADHOC_DIR>/df_documents_missing_input.csv \
    --output-dir <ADHOC_DIR> \
    --output-file df_documents_general_v2_patch.csv \
    --model gpt-5.4-mini-2026-03-17 --prompt-variant simple_v2 \
    --submit --post-process --max-output-tokens 16384

Usage
-----
  python patch_missing_general_agreement.py build-input
  python patch_missing_general_agreement.py append
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import pandas as pd

OUTPUT_ROOT = Path("/data/home/xiong/data/Fund/CSR/Tractions/output")
INCR_DIR = OUTPUT_ROOT / "incremental_update" / "06_07_2026_update"
PREV_INCR_DIR = OUTPUT_ROOT / "incremental_update" / "05252026_update"
ADHOC_DIR = OUTPUT_ROOT / "adhoc" / "general_agreement_v2"

# Source of the core/general merged pair used to compute the gap set.
CORE_MERGED = INCR_DIR / "df_fin_reg_core_merged.csv"
GENERAL_MERGED = INCR_DIR / "df_documents_general_merged.csv"

# Doc-level staff/buff text for the 2024 gap docs lives in the previous run's
# incremental doc rollup; the 2017 CEMAC doc has only staff paragraphs (below).
PREV_DF_DOCUMENTS = PREV_INCR_DIR / "df_documents_incremental.csv"
CEMAC_ISBN = "9781484305775"
CEMAC_PARAGRAPHS = INCR_DIR / "df_paragraphs_incremental.csv"

# The general-agreement input schema (matches df_documents.csv exactly).
DOC_INPUT_COLS = ["index", "Print ISBN", "staff", "buff", "country", "year", "publication_date"]

MISSING_INPUT_CSV = ADHOC_DIR / "df_documents_missing_input.csv"
EXCLUDED_CSV = ADHOC_DIR / "patch_excluded_docs.csv"
PATCH_RESULTS_CSV = ADHOC_DIR / "df_documents_general_v2_patch.csv"
TARGET_CSV = ADHOC_DIR / "df_documents_general_v2.csv"
TARGET_BACKUP = ADHOC_DIR / "df_documents_general_v2.prepatch.bak.csv"


def _norm(s: pd.Series) -> pd.Series:
    """Normalize Print ISBN so int/float/str variants compare equal (strip a trailing .0)."""
    return s.astype(str).str.replace(r"\.0$", "", regex=True)


def _gap_isbns() -> set[str]:
    core = pd.read_csv(CORE_MERGED)
    gen = pd.read_csv(GENERAL_MERGED)
    core_i = set(_norm(core["Print ISBN"]))
    gen_i = set(_norm(gen["Print ISBN"]))
    return core_i - gen_i


def _reconstruct_cemac_row() -> dict | None:
    """Build a doc-level row for the CEMAC doc from its paragraphs.

    staff = staff report + staff appraisal paragraphs; buff = authorities' views +
    buff statement. CEMAC has only staff-side paragraphs, so buff comes out empty
    and the doc will be dropped by the staff-and-buff filter downstream (reported,
    not fabricated). We still assemble the row so the exclusion is explicit.
    """
    if not CEMAC_PARAGRAPHS.exists():
        return None
    par = pd.read_csv(CEMAC_PARAGRAPHS, low_memory=False)
    par["isbn"] = _norm(par["Print ISBN"])
    c = par[par["isbn"] == CEMAC_ISBN]
    if c.empty:
        return None
    staff_types = {"staff", "staff_a"}
    buff_types = {"buff", "buff_a"}
    staff = "\n".join(c.loc[c["type"].isin(staff_types), "text"].astype(str))
    buff = "\n".join(c.loc[c["type"].isin(buff_types), "text"].astype(str))
    return {
        "Print ISBN": c["Print ISBN"].iloc[0],
        "staff": staff,
        "buff": buff,
        "country": "Central African Economic and Monetary Community (CEMAC)",
        "year": 2017,
        "publication_date": pd.NA,
    }


def build_input() -> None:
    ADHOC_DIR.mkdir(parents=True, exist_ok=True)
    gap = _gap_isbns()
    print(f"Gap docs (in core, absent from general): {len(gap)}")

    # --- 2024 docs: pull staff/buff text from the previous run's doc rollup ---
    prev = pd.read_csv(PREV_DF_DOCUMENTS, low_memory=False)
    prev["isbn"] = _norm(prev["Print ISBN"])
    rows = prev[prev["isbn"].isin(gap)].copy()
    from_prev = set(rows["isbn"])
    print(f"  found in {PREV_DF_DOCUMENTS.name}: {len(from_prev)}")

    # --- CEMAC 2017: reconstruct from paragraphs (staff-only; buff will be empty) ---
    still_missing = gap - from_prev
    cemac = None
    if CEMAC_ISBN in still_missing:
        cemac = _reconstruct_cemac_row()
        if cemac is not None:
            rows = pd.concat([rows, pd.DataFrame([cemac])], ignore_index=True)
            still_missing = still_missing - {CEMAC_ISBN}
            print(f"  reconstructed {CEMAC_ISBN} (CEMAC) from paragraphs")
    if still_missing:
        print(f"  WARNING: {len(still_missing)} gap docs have no text source at all: {sorted(still_missing)}")

    # --- apply the SAME staff-and-buff filter the inference uses, so we know up
    #     front which docs are actually scoreable and can report the rest ---
    rows["isbn"] = _norm(rows["Print ISBN"])
    staff_ok = rows["staff"].notna() & rows["staff"].astype(str).str.strip().ne("")
    buff_ok = rows["buff"].notna() & rows["buff"].astype(str).str.strip().ne("")
    scoreable = rows[staff_ok & buff_ok].copy()
    excluded = rows[~(staff_ok & buff_ok)].copy()

    # --- write the excluded report ---
    if len(excluded):
        exc = excluded[["Print ISBN", "country", "year"]].copy()
        exc["reason"] = [
            "no_buff_text" if (not b) else ("no_staff_text" if (not s) else "missing_text")
            for s, b in zip(staff_ok[~(staff_ok & buff_ok)], buff_ok[~(staff_ok & buff_ok)])
        ]
        exc.to_csv(EXCLUDED_CSV, index=False)
        print(f"\nExcluded {len(exc)} doc(s) (missing one side of the bilateral text):")
        print(exc.to_string(index=False))
        print(f"  -> {EXCLUDED_CSV}")
    else:
        print("\nNo docs excluded — all gap docs have both staff and buff text.")

    # --- write the scoreable input in the exact df_documents schema ---
    scoreable = scoreable.reset_index(drop=True)
    scoreable["index"] = scoreable.index
    out = scoreable[DOC_INPUT_COLS]
    out.to_csv(MISSING_INPUT_CSV, index=False)
    print(f"\nWrote {len(out)} scoreable rows -> {MISSING_INPUT_CSV}")

    # sanity assertions
    assert out["Print ISBN"].nunique() == len(out), "duplicate ISBNs in input"
    assert (out["staff"].astype(str).str.strip() != "").all(), "empty staff slipped through"
    assert (out["buff"].astype(str).str.strip() != "").all(), "empty buff slipped through"
    print("Sanity checks passed (unique ISBNs, non-empty staff & buff).")

    print("\nNEXT: run the inference (separate manual step), then `append`:")
    print(
        "  python ../../inference_general_agreement.py \\\n"
        f"    --data-file {MISSING_INPUT_CSV} \\\n"
        f"    --output-dir {ADHOC_DIR} \\\n"
        "    --output-file df_documents_general_v2_patch.csv \\\n"
        "    --model gpt-5.4-mini-2026-03-17 --prompt-variant simple_v2 \\\n"
        "    --submit --post-process --max-output-tokens 16384"
    )


def append() -> None:
    if not PATCH_RESULTS_CSV.exists():
        sys.exit(f"Patch results not found: {PATCH_RESULTS_CSV}\nRun the inference step first.")
    if not TARGET_BACKUP.exists():
        shutil.copy2(TARGET_CSV, TARGET_BACKUP)
        print(f"Backed up target -> {TARGET_BACKUP}")

    target = pd.read_csv(TARGET_CSV, low_memory=False)
    patch = pd.read_csv(PATCH_RESULTS_CSV, low_memory=False)
    target["isbn"] = _norm(target["Print ISBN"])
    patch["isbn"] = _norm(patch["Print ISBN"])

    before = len(target)
    dupes = set(target["isbn"]) & set(patch["isbn"])
    if dupes:
        print(f"Skipping {len(dupes)} patch rows already present in target (idempotent).")
        patch = patch[~patch["isbn"].isin(dupes)]

    # align columns to target's order; concat; renumber id as a clean ordinal
    patch = patch.reindex(columns=[c for c in target.columns if c != "isbn"])
    combined = pd.concat(
        [target.drop(columns=["isbn"]), patch], ignore_index=True
    )
    if "id" in combined.columns:
        combined["id"] = combined.index.astype(str)
    if "index" in combined.columns:
        combined["index"] = combined.index

    combined.to_csv(TARGET_CSV, index=False)
    print(f"Appended {len(combined) - before} rows: {before} -> {len(combined)} ({TARGET_CSV})")
    assert combined["Print ISBN"].nunique() == len(combined), "duplicate ISBNs after append"
    print("Sanity check passed (unique ISBNs).")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("phase", choices=["build-input", "append"])
    args = ap.parse_args()
    if args.phase == "build-input":
        build_input()
    else:
        append()


if __name__ == "__main__":
    main()
