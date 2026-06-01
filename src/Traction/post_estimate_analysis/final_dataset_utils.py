"""
Shared logic for building the document-level final analysis dataset.

This module is the single source of truth for the transformation that turns
inference outputs (`agreement_*_results.csv`, `stance_*_results.csv`,
`df_documents_general*.csv`) plus document metadata (`df_aiv*.csv`) into the
final analysis-ready frames.

Two callers consume it:
  - `src/Traction/create_final_dataset.py` (main-pipeline rerun; writes
    `df_fin.csv` + `df_fin_reg_core.csv`).
  - `src/Traction/incremental_update/07b_create_final_dataset_incremental.py`
    (incremental run; writes `df_fin_incremental.csv` +
    `df_fin_core_incremental.csv`).

The two callers differ only in:
  - input directory
  - input filenames (e.g. `df_aiv.csv` vs `df_aiv_incremental.csv`)
  - output filenames

so this module is parameterised on `source_dir` and explicit filenames, and the
incremental-vs-main distinction lives entirely at the call site.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

# Allow this module to import data_vis_utils from the same directory whether it's
# loaded as a package member or executed against an extended sys.path.
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
import data_vis_utils as dv  # noqa: E402

_TRACTION_DIR = _THIS_DIR.parent
DEFAULT_COUNTRY_META_PATH = _TRACTION_DIR / "docs" / "reference" / "country_meta_info.xlsx"

# ---------------------------------------------------------------------------
# Numeric encodings
# ---------------------------------------------------------------------------

STANCE_FUTURE_DICT = {
    "tightening": 5,
    "tightening bias": 4,
    "no change": 3,
    "loosening bias": 2,
    "loosening": 1,
}
STANCE_CURRENT_DICT = {"accommodative": 0, "neutral": 1, "restrictive": 2}

# Policy-mix coding (mirrors `09_analysis_full_sample.ipynb`).
_POLICY_MIX_SHORT = {
    "tightening": "t",
    "tightening bias": "t",
    "no change": "n",
    "unclear": "n",
    "loosening bias": "l",
    "loosening": "l",
}

# ---------------------------------------------------------------------------
# Column rename maps
# ---------------------------------------------------------------------------

# Internal short names → legacy `_gpt_ft` column names (matches archive
# `df_fin_reg_core.csv` schema).
RENAME_MAP = {
    "mon_stance_current_staff": "mon_stance_current_gpt_ft_staff",
    "mon_stance_future_staff": "mon_stance_future_gpt_ft_staff",
    "mon_stance_current_buff": "mon_stance_current_gpt_ft_buff",
    "mon_stance_future_buff": "mon_stance_future_gpt_ft_buff",
    "mon_agreement": "mon_agreement_gpt_ft",
    "mon_disagreement_areas": "mon_disagreement_areas_gpt_ft",
    "fis_agreement": "fis_agreement_gpt_ft",
    "fis_disagreement_areas": "fis_disagreement_areas_gpt_ft",
    "fis_stance_near_term_staff": "fis_stance_near_term_gpt_ft_staff",
    "fis_stance_near_term_buff": "fis_stance_near_term_gpt_ft_buff",
    "mon_stance_future_staff_num": "mon_stance_future_gpt_ft_staff_num",
    "mon_stance_future_buff_num": "mon_stance_future_gpt_ft_buff_num",
    "mon_agreement_stance_future_num": "mon_agreement_stance_future_gpt_ft_num",
    "mon_agreement_stance_future_cate1": "mon_agreement_stance_future_gpt_ft_cate1",
    "mon_agreement_stance_future_cate2": "mon_agreement_stance_future_gpt_ft_cate2",
    "mon_stance_current_staff_num": "mon_stance_current_gpt_ft_staff_num",
    "mon_stance_current_buff_num": "mon_stance_current_gpt_ft_buff_num",
    "mon_agreement_stance_current_num": "mon_agreement_stance_current_gpt_ft_num",
    "mon_agreement_stance_current_cate2": "mon_agreement_stance_current_gpt_ft_cate2",
    "mon_agreement_stance_current": "mon_agreement_stance_current_gpt_ft",
    "mon_agreement_stance_future": "mon_agreement_stance_future_gpt_ft",
    "mon_agreement_general": "mon_agreement_general_gpt_ft",
    "fis_stance_near_term_staff_num": "fis_stance_near_term_gpt_ft_staff_num",
    "fis_stance_near_term_buff_num": "fis_stance_near_term_gpt_ft_buff_num",
    "fis_agreement_stance_near_term_num": "fis_agreement_stance_near_term_gpt_ft_num",
    "fis_agreement_stance_near_term_cate1": "fis_agreement_stance_near_term_gpt_ft_cate1",
    "fis_agreement_stance_near_term_cate2": "fis_agreement_stance_near_term_gpt_ft_cate2",
    "fis_agreement_stance_near_term": "fis_agreement_stance_near_term_gpt_ft",
    "fis_agreement_general": "fis_agreement_general_gpt_ft",
    "fis_disagreement_areas_general": "fis_disagreement_areas_general_gpt_ft",
    "agreement_overall": "agreement_gpt_ft",
}

ZERO_SHOT_RENAME = {
    "Agreement_General": "agreement_gpt",
    "Agreement_Monetary": "agreement_gpt_Monetary",
    "Agreement_Fiscal": "agreement_gpt_Fiscal",
    "Agreement_External": "agreement_gpt_External",
    "Agreement_Financial": "agreement_gpt_Financial",
    "Agreement_Real": "agreement_gpt_Real",
}

# Columns in df_fin_reg_core.csv (the target schema for the core output).
CORE_COLUMNS = [
    "Print ISBN", "country", "Primary Country Code", "year",
    "publication_date", "bm_date",
    "agreement_gpt", "agreement_gpt_Monetary", "agreement_gpt_Fiscal",
    "agreement_gpt_External", "agreement_gpt_Financial", "agreement_gpt_Real",
    "mon_stance_current_gpt_ft_staff", "mon_stance_future_gpt_ft_staff",
    "mon_stance_current_gpt_ft_buff", "mon_stance_future_gpt_ft_buff",
    "mon_agreement_gpt_ft", "mon_disagreement_areas_gpt_ft",
    "fis_agreement_gpt_ft", "fis_disagreement_areas_gpt_ft",
    "fis_stance_near_term_gpt_ft_staff", "fis_stance_near_term_gpt_ft_buff",
    "mon_stance_future_gpt_ft_staff_num", "mon_stance_future_gpt_ft_buff_num",
    "mon_agreement_stance_future_gpt_ft_num",
    "mon_agreement_stance_future_gpt_ft_cate1",
    "mon_agreement_stance_future_gpt_ft_cate2",
    "mon_stance_current_gpt_ft_staff_num", "mon_stance_current_gpt_ft_buff_num",
    "mon_agreement_stance_current_gpt_ft_num",
    "mon_agreement_stance_current_gpt_ft_cate2",
    "mon_agreement_stance_current_gpt_ft",
    "mon_agreement_stance_future_gpt_ft",
    "mon_agreement_general_gpt_ft",
    "fis_stance_near_term_gpt_ft_staff_num", "fis_stance_near_term_gpt_ft_buff_num",
    "fis_agreement_stance_near_term_gpt_ft_num",
    "fis_agreement_stance_near_term_gpt_ft_cate1",
    "fis_agreement_stance_near_term_gpt_ft_cate2",
    "fis_agreement_stance_near_term_gpt_ft",
    "fis_agreement_general_gpt_ft",
    "fis_disagreement_areas_general_gpt_ft",
    "disagree_economic", "agreement_gpt_ft",
]


# ---------------------------------------------------------------------------
# Transformation helpers
# ---------------------------------------------------------------------------

def _normalize_areas(val) -> list:
    """Normalize disagreement_areas to a lowercase list, matching legacy format."""
    if isinstance(val, list):
        return [v.lower().strip() for v in val]
    if not isinstance(val, str) or pd.isna(val):
        return []
    if val.startswith("["):
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, list):
                return [v.lower().strip() for v in parsed]
        except (ValueError, SyntaxError):
            pass
    return [item.lower().strip() for item in val.split(";") if item.strip()]


def _clean_nan_str(series: pd.Series, fill: str = "irrelevant") -> pd.Series:
    out = series.fillna(fill)
    return out.apply(lambda x: fill if str(x).strip().lower() in ["nan", ""] else x)


def _derive_monetary(df_mon_wide: pd.DataFrame) -> pd.DataFrame:
    df = df_mon_wide.copy()

    for col in ["mon_stance_current_staff", "mon_stance_current_buff",
                "mon_stance_future_staff", "mon_stance_future_buff"]:
        df[col] = _clean_nan_str(df[col])

    for col in ["mon_stance_current_staff", "mon_stance_current_buff"]:
        df[col] = df[col].apply(
            lambda x: "restrictive" if x in ["moderately tight", "tightening bias"]
            else "neutral" if x in ["close to neutral"]
            else x
        )

    df["mon_stance_future_staff_num"] = df["mon_stance_future_staff"].map(STANCE_FUTURE_DICT)
    df["mon_stance_future_buff_num"] = df["mon_stance_future_buff"].map(STANCE_FUTURE_DICT)
    df["mon_agreement_stance_future_num"] = (
        df["mon_stance_future_staff_num"] - df["mon_stance_future_buff_num"]
    )

    df["mon_agreement_stance_future_cate1"] = df["mon_agreement_stance_future_num"].apply(
        lambda x: "major difference" if abs(x) >= 3 else "some difference" if abs(x) == 2
        else "minor difference" if abs(x) == 1 else "no difference" if x == 0 else "irrelevant"
        if pd.isna(x) else "irrelevant"
    )
    df["mon_agreement_stance_future_cate2"] = df["mon_agreement_stance_future_num"].apply(
        lambda x: "significantly tighter" if x >= 3 else "tighter" if x == 2
        else "moderately tighter" if x == 1 else "same" if x == 0
        else "moderately looser" if x == -1 else "looser" if x == -2
        else "significantly looser" if x <= -3 else "irrelevant"
        if pd.isna(x) else "irrelevant"
    )

    df["mon_stance_current_staff_num"] = df["mon_stance_current_staff"].map(STANCE_CURRENT_DICT)
    df["mon_stance_current_buff_num"] = df["mon_stance_current_buff"].map(STANCE_CURRENT_DICT)
    df["mon_agreement_stance_current_num"] = (
        df["mon_stance_current_staff_num"] - df["mon_stance_current_buff_num"]
    )

    df["mon_agreement_stance_current_cate2"] = df["mon_agreement_stance_current_num"].apply(
        lambda x: "same" if x == 0 else "more accommodative" if x < 0
        else "more restrictive" if x > 0 else "irrelevant"
    )

    def _agree_current(row):
        s, b = row["mon_stance_current_staff"], row["mon_stance_current_buff"]
        for v in [s, b]:
            if v in ["", "nan", "n", "unclear", "irrelevant"] or pd.isna(v):
                return "irrelevant"
        return "mostly agree" if s == b else "disagreement exists"

    df["mon_agreement_stance_current"] = df.apply(_agree_current, axis=1)

    def _agree_future(row):
        s, b = row["mon_stance_future_staff"], row["mon_stance_future_buff"]
        for v in [s, b]:
            if v in ["", "nan", "n", "unclear", "irrelevant"] or pd.isna(v):
                return "irrelevant"
        diff = row["mon_agreement_stance_future_num"]
        if pd.isna(diff):
            return "irrelevant"
        return "mostly agree" if abs(diff) <= 1 else "disagreement exists"

    df["mon_agreement_stance_future"] = df.apply(_agree_future, axis=1)

    return df


def _derive_fiscal(df_fis_wide: pd.DataFrame) -> pd.DataFrame:
    df = df_fis_wide.copy()

    for col in ["fis_stance_near_term_staff", "fis_stance_near_term_buff"]:
        df[col] = _clean_nan_str(df[col])

    df["fis_stance_near_term_staff_num"] = df["fis_stance_near_term_staff"].map(STANCE_FUTURE_DICT)
    df["fis_stance_near_term_buff_num"] = df["fis_stance_near_term_buff"].map(STANCE_FUTURE_DICT)
    df["fis_agreement_stance_near_term_num"] = (
        df["fis_stance_near_term_staff_num"] - df["fis_stance_near_term_buff_num"]
    )

    df["fis_agreement_stance_near_term_cate1"] = df["fis_agreement_stance_near_term_num"].apply(
        lambda x: "major difference" if abs(x) >= 3 else "some difference" if abs(x) == 2
        else "minor difference" if abs(x) == 1 else "no difference" if x == 0 else "irrelevant"
        if pd.isna(x) else "irrelevant"
    )
    df["fis_agreement_stance_near_term_cate2"] = df["fis_agreement_stance_near_term_num"].apply(
        lambda x: "significantly tighter" if x >= 3 else "tighter" if x == 2
        else "moderately tighter" if x == 1 else "same" if x == 0
        else "moderately looser" if x == -1 else "looser" if x == -2
        else "significantly looser" if x <= -3 else "irrelevant"
        if pd.isna(x) else "irrelevant"
    )

    def _agree_near_term(row):
        s, b = row["fis_stance_near_term_staff"], row["fis_stance_near_term_buff"]
        for v in [s, b]:
            if v in ["", "nan", "n", "unclear", "irrelevant"] or pd.isna(v):
                return "irrelevant"
        diff = row["fis_agreement_stance_near_term_num"]
        if pd.isna(diff):
            return "irrelevant"
        return "mostly agree" if abs(diff) <= 1 else "disagreement exists"

    df["fis_agreement_stance_near_term"] = df.apply(_agree_near_term, axis=1)

    return df


def _mon_general_agree(row):
    stance_cur = row.get("mon_agreement_stance_current", "irrelevant")
    stance_fut = row.get("mon_agreement_stance_future", "irrelevant")
    text_agree = row.get("mon_agreement", np.nan)
    fut_num = row.get("mon_agreement_stance_future_num", np.nan)
    disag_area = row.get("mon_disagreement_areas", "")

    if stance_cur == "irrelevant" and stance_fut == "irrelevant" and (
        pd.isna(text_agree) or text_agree == "irrelevant"
    ):
        return "irrelevant"

    if (stance_cur == "disagreement exists"
        or (not pd.isna(fut_num) and abs(fut_num) > 1)
        or (text_agree == "disagreement exists"
            and str(disag_area) != "Future Policy Direction")):
        return "disagreement exists"

    return "mostly agree"


def _fis_general_agree(row):
    stance_nt = row.get("fis_agreement_stance_near_term", "irrelevant")
    text_agree = row.get("fis_agreement", np.nan)
    nt_num = row.get("fis_agreement_stance_near_term_num", np.nan)
    disag_area = row.get("fis_disagreement_areas", "")

    if stance_nt == "irrelevant" and (pd.isna(text_agree) or text_agree == "irrelevant"):
        return "irrelevant"

    if ((not pd.isna(nt_num) and abs(nt_num) > 1)
        or (text_agree == "disagreement exists"
            and str(disag_area) != "['near-term policy direction']")):
        return "disagreement exists"

    return "mostly agree"


def _safe_contains(val, target: str) -> bool:
    """Check if target string is in val, handling lists and strings."""
    if isinstance(val, list):
        return target in val
    try:
        if pd.isna(val):
            return False
    except (ValueError, TypeError):
        pass
    s = str(val)
    if s.startswith("["):
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, list):
                return target in parsed
        except (ValueError, SyntaxError):
            pass
    return target in s.lower()


def _policy_mix_label(mon_val, fis_val):
    m = _POLICY_MIX_SHORT.get(str(mon_val).strip().lower())
    f = _POLICY_MIX_SHORT.get(str(fis_val).strip().lower())
    if m is None or f is None:
        return None
    return f"M{m}F{f}"


def _derive_policy_mix(df: pd.DataFrame) -> pd.DataFrame:
    """Add `policy_mix_staff` / `policy_mix_buff` columns (9-category combos).

    Operates on the post-rename DataFrame (i.e. columns already use the legacy
    `_gpt_ft` suffix). Skipped silently if the source stance columns are
    missing.
    """
    mon_staff = "mon_stance_future_gpt_ft_staff"
    mon_buff = "mon_stance_future_gpt_ft_buff"
    fis_staff = "fis_stance_near_term_gpt_ft_staff"
    fis_buff = "fis_stance_near_term_gpt_ft_buff"

    if all(c in df.columns for c in [mon_staff, fis_staff]):
        df["policy_mix_staff"] = [
            _policy_mix_label(m, f) for m, f in zip(df[mon_staff], df[fis_staff])
        ]
    if all(c in df.columns for c in [mon_buff, fis_buff]):
        df["policy_mix_buff"] = [
            _policy_mix_label(m, f) for m, f in zip(df[mon_buff], df[fis_buff])
        ]
    return df


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_final_dataset(
    source_dir: Path,
    *,
    aiv_filename: str,
    agreement_monetary_filename: str = "agreement_monetary_results.csv",
    agreement_fiscal_filename: str = "agreement_fiscal_results.csv",
    stance_monetary_filename: str = "stance_monetary_results.csv",
    stance_fiscal_filename: str = "stance_fiscal_results.csv",
    general_agreement_filename: str | None = None,
    start_year: int = 2015,
    end_year: int | None = None,
    country_meta_path: Path = DEFAULT_COUNTRY_META_PATH,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Build (full_df, core_df) from inference outputs in `source_dir`.

    Returns
    -------
    (df_fin_full, df_fin_core)
        - `df_fin_full` includes text columns and the `policy_mix_*` derivations.
        - `df_fin_core` is the subset matching the archive's
          `df_fin_reg_core.csv` schema (no `policy_mix_*`).
    """
    source_dir = Path(source_dir).resolve()
    print(f"Source dir: {source_dir}")
    print(f"Year range: {start_year} – {end_year or 'no upper bound'}")

    # ── 1. Load & filter df_aiv ───────────────────────────────────────────
    df_aiv = pd.read_csv(source_dir / aiv_filename)
    n_total = len(df_aiv)
    df_aiv = df_aiv[df_aiv["staff_verified"] == True].copy()  # noqa: E712
    print(f"  {aiv_filename}: {n_total} total, {len(df_aiv)} staff_verified")

    df_aiv["year"] = pd.to_numeric(df_aiv["Year from title"], errors="coerce").astype("Int64")
    df_aiv = df_aiv[df_aiv["year"].notna()].copy()
    df_aiv["year"] = df_aiv["year"].astype(int)
    if start_year:
        df_aiv = df_aiv[df_aiv["year"] >= start_year]
    if end_year:
        df_aiv = df_aiv[df_aiv["year"] <= end_year]
    print(f"  After year filter: {len(df_aiv)} docs")

    country_map = pd.read_excel(country_meta_path)
    df_aiv = df_aiv.merge(country_map, left_on="Primary Country Code",
                          right_on="ISO3", how="left")
    df_aiv["income_group"] = df_aiv["Income"]

    # The incremental pipeline adds `Primary Country Description` during step 02
    # postprocessing; the main `df_aiv.csv` does not. Fall back to the
    # country_meta `Country` value (joined above on ISO3) so the downstream
    # `country` column is always populated.
    if "Primary Country Description" not in df_aiv.columns:
        df_aiv["Primary Country Description"] = df_aiv["Country"]

    # ── 2. Load inference results ─────────────────────────────────────────
    df_agree_mon = pd.read_csv(source_dir / agreement_monetary_filename)
    df_agree_fis = pd.read_csv(source_dir / agreement_fiscal_filename)
    df_stance_mon = pd.read_csv(source_dir / stance_monetary_filename)
    df_stance_fis = pd.read_csv(source_dir / stance_fiscal_filename)

    # Clean hallucinated fiscal agreement values seen in past runs.
    df_agree_fis["agreement"] = df_agree_fis["agreement"].apply(
        lambda x: "mostly agree" if x in ["Micah mostly agree", "appropriately agree", "валлийский"]
        else x
    )

    # ── 3. Pivot stance long → wide ──────────────────────────────────────
    df_mon_wide = dv.pivot_stance_wide(
        df_stance_mon, author_col="type",
        stance_cols=["stance_current", "stance_future"],
    )
    df_mon_wide = df_mon_wide.rename(columns={
        "staff_stance_current": "mon_stance_current_staff",
        "buff_stance_current": "mon_stance_current_buff",
        "staff_stance_future": "mon_stance_future_staff",
        "buff_stance_future": "mon_stance_future_buff",
    })

    df_fis_wide = dv.pivot_stance_wide(
        df_stance_fis, author_col="type",
        stance_cols=["stance_near_term"],
    )
    df_fis_wide = df_fis_wide.rename(columns={
        "staff_stance_near_term": "fis_stance_near_term_staff",
        "buff_stance_near_term": "fis_stance_near_term_buff",
    })

    # ── 4. Derive stance variables ───────────────────────────────────────
    df_mon_wide = _derive_monetary(df_mon_wide)
    df_fis_wide = _derive_fiscal(df_fis_wide)

    # ── 5. Merge into single document-level DataFrame ────────────────────
    df = df_aiv[["Print ISBN", "year", "Primary Country Code",
                 "Primary Country Description", "Publication Date",
                 "has_buff"]].copy()
    df = df.rename(columns={
        "Primary Country Description": "country",
        "Publication Date": "publication_date",
    })
    df["bm_date"] = np.nan

    text_cols = [c for c in df_aiv.columns if c in [
        "text_staff", "text_buff", "text_sa",
        "paragraphs_sa", "paragraphs_bu", "paragraphs_sr", "paragraphs_av",
        "staff_verified", "buff_verified", "income_group",
        "Title", "Full Title",
    ]]
    for col in text_cols:
        df[col] = df_aiv[col].values

    # Monetary agreement
    df = df.merge(
        df_agree_mon[["Print ISBN", "agreement", "disagreement_areas"]].rename(columns={
            "agreement": "mon_agreement",
            "disagreement_areas": "mon_disagreement_areas",
        }),
        on="Print ISBN", how="left",
    )
    df["mon_agreement"] = _clean_nan_str(df["mon_agreement"])
    df["mon_disagreement_areas"] = df["mon_disagreement_areas"].apply(_normalize_areas)

    # Fiscal agreement
    df = df.merge(
        df_agree_fis[["Print ISBN", "agreement", "disagreement_areas"]].rename(columns={
            "agreement": "fis_agreement",
            "disagreement_areas": "fis_disagreement_areas",
        }),
        on="Print ISBN", how="left",
    )
    df["fis_agreement"] = _clean_nan_str(df["fis_agreement"])
    df["fis_disagreement_areas"] = df["fis_disagreement_areas"].apply(_normalize_areas)

    # Stance wide tables
    mon_cols = [c for c in df_mon_wide.columns if c.startswith("mon_") or c == "Print ISBN"]
    df = df.merge(df_mon_wide[mon_cols], on="Print ISBN", how="left")
    fis_cols = [c for c in df_fis_wide.columns if c.startswith("fis_") or c == "Print ISBN"]
    df = df.merge(df_fis_wide[fis_cols], on="Print ISBN", how="left")

    # ── 6. Merge zero-shot general agreement ─────────────────────────────
    if general_agreement_filename:
        zs_path = source_dir / general_agreement_filename
    else:
        zs_path = None
    if zs_path and zs_path.exists():
        df_zs = pd.read_csv(zs_path)
        zs_cols = ["Print ISBN"] + list(ZERO_SHOT_RENAME.keys())
        zs_cols = [c for c in zs_cols if c in df_zs.columns]
        df = df.merge(df_zs[zs_cols].rename(columns=ZERO_SHOT_RENAME), on="Print ISBN", how="left")
        for col in ZERO_SHOT_RENAME.values():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                df.loc[df[col] == 99, col] = np.nan
        print(f"  Merged zero-shot general agreement: {len(df_zs)} rows")
    else:
        print(f"  WARNING: zero-shot general agreement file not found, skipping merge")
        for col in ZERO_SHOT_RENAME.values():
            df[col] = np.nan

    # ── 7. General agreement variables ───────────────────────────────────
    df["mon_agreement_general"] = df.apply(_mon_general_agree, axis=1)
    df["fis_agreement_general"] = df.apply(_fis_general_agree, axis=1)

    df["fis_disagreement_areas_general"] = df["fis_disagreement_areas"].copy()
    mask_fis_stance_disagree = df["fis_agreement_stance_near_term"] == "disagreement exists"
    for idx in df[mask_fis_stance_disagree].index:
        areas = df.at[idx, "fis_disagreement_areas_general"]
        if not isinstance(areas, list):
            areas = [] if pd.isna(areas) else [str(areas)]
        if "near-term policy direction" not in areas:
            df.at[idx, "fis_disagreement_areas_general"] = areas + ["near-term policy direction"]

    # ── 8. Binarize key agreement columns ────────────────────────────────
    df = df.rename(columns=RENAME_MAP)

    key_cols = [
        "agreement_gpt", "agreement_gpt_Monetary", "agreement_gpt_Fiscal",
        "agreement_gpt_External", "agreement_gpt_Financial", "agreement_gpt_Real",
        "mon_agreement_gpt_ft", "mon_agreement_stance_future_gpt_ft_num",
        "mon_agreement_general_gpt_ft",
        "fis_agreement_gpt_ft", "fis_agreement_stance_near_term_gpt_ft_num",
        "fis_agreement_general_gpt_ft",
    ]

    for col in key_cols:
        if col not in df.columns:
            continue
        df[col] = df[col].apply(lambda x: np.nan if x == 99 else x)
        df[col] = df[col].apply(
            lambda x: np.nan if x == "irrelevant"
            else 0 if x == "disagreement exists"
            else 1 if x == "mostly agree"
            else x
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── 9. Derived overall variables ─────────────────────────────────────
    df["disagree_economic"] = df.apply(
        lambda r: (_safe_contains(r.get("mon_disagreement_areas_gpt_ft", ""), "economic assessment")
                   or _safe_contains(r.get("fis_disagreement_areas_gpt_ft", ""), "economic assessment")),
        axis=1,
    )

    df["agreement_gpt_ft"] = (
        (df["mon_agreement_general_gpt_ft"] + df["fis_agreement_general_gpt_ft"] == 2)
        | ((df["mon_agreement_general_gpt_ft"].isna()) & (df["fis_agreement_general_gpt_ft"] == 1))
        | ((df["fis_agreement_general_gpt_ft"].isna()) & (df["mon_agreement_general_gpt_ft"] == 1))
    )

    # ── 10. Policy-mix labels (full output only) ─────────────────────────
    df = _derive_policy_mix(df)

    # ── 11. Build core subset ────────────────────────────────────────────
    core_cols_present = [c for c in CORE_COLUMNS if c in df.columns]
    missing_core = [c for c in CORE_COLUMNS if c not in df.columns]
    if missing_core:
        print(f"  WARNING: Core columns missing: {missing_core}")
    df_core = df[core_cols_present].copy()

    print(f"  Full shape: {df.shape}")
    print(f"  Core shape: {df_core.shape}")

    return df, df_core
