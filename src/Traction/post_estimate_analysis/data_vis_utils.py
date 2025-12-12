"""Utilities for post-estimation visualizations.

This module is extracted from experiments in `data_vis.ipynb` and is intentionally
parameterized so it can be reused for monetary, fiscal, and other sectors.

Design goals:
- **Sector-agnostic**: pass column names / mappings instead of hard-coding.
- **Composable**: small helpers that return DataFrames/axes rather than doing I/O.
- **Notebook-friendly**: minimal dependencies (pandas/numpy/matplotlib).
"""

from __future__ import annotations

from typing import Any, Callable, Collection, Mapping, Sequence

import re

import numpy as np  # type: ignore[import-not-found]
import pandas as pd  # type: ignore[import-not-found]

__all__ = [
    # income groups / country helpers
    "AE_COUNTRY_CODES",
    "EM_COUNTRY_CODES",
    "COUNTRY_NAME_TO_CODE",
    "country_name_to_iso3",
    "classify_income_group_from_code",
    "classify_income_group_from_country_name",
    # generic dataframe helpers
    "coerce_year_int",
    "filter_year_range",
    "compute_year_group_counts",
    # plotting helpers
    "style_axes",
    "plot_stacked_counts_by_year",
    "plot_group_lines_by_year",
    "plot_category_trends",
    "plot_stacked_proportions_by_year",
    # agreement helpers
    "add_no_disagreement_flag",
    "compute_no_disagreement_proportions_by_year",
    # disagreement area helpers
    "extract_categories_from_text",
    "add_extracted_categories",
    "explode_categories",
    "compute_category_percentage_by_year",
    # stance helpers
    "pivot_stance_wide",
    "STANCE_DIRECTION_SCORE_DEFAULT",
    "bucket_imf_vs_auth_diff",
    "DEFAULT_IMF_VS_AUTH_ORDER",
    "compute_imf_vs_authority_share",
]


# ----------------------------
# Income group helpers
# ----------------------------

AE_COUNTRY_CODES: frozenset[str] = frozenset(
    {
        "USA",
        "GBR",
        "DEU",
        "FRA",
        "JPN",
        "CAN",
        "ITA",
        "ESP",
        "AUS",
        "NLD",
        "BEL",
        "SWE",
        "CHE",
        "NOR",
        "DNK",
        "AUT",
        "FIN",
        "IRL",
        "NZL",
        "SGP",
        "HKG",
        "ISR",
        "KOR",
        "PRT",
        "GRC",
        "CZE",
        "SVK",
        "SVN",
        "EST",
        "LVA",
        "LTU",
        "CYP",
        "MLT",
        "ISL",
        "LUX",
    }
)

EM_COUNTRY_CODES: frozenset[str] = frozenset(
    {
        "CHN",
        "IND",
        "BRA",
        "RUS",
        "MEX",
        "IDN",
        "TUR",
        "SAU",
        "ARG",
        "ZAF",
        "THA",
        "MYS",
        "PHL",
        "POL",
        "EGY",
        "PAK",
        "VNM",
        "BGD",
        "NGA",
        "IRQ",
        "COL",
        "CHL",
        "ROU",
        "PER",
        "UKR",
        "MAR",
        "KAZ",
        "QAT",
        "ARE",
        "KWT",
        "HUN",
        "DZA",
        "OMN",
        "HRV",
        "BLR",
        "BGR",
    }
)

# NOTE: This is a simplified mapping mirroring the notebook.
# You may want to replace/extend this with an authoritative ISO mapping later.
COUNTRY_NAME_TO_CODE: dict[str, str] = {
    "United States": "USA",
    "United Kingdom": "GBR",
    "Germany": "DEU",
    "France": "FRA",
    "Japan": "JPN",
    "Canada": "CAN",
    "Italy": "ITA",
    "Spain": "ESP",
    "Australia": "AUS",
    "Netherlands": "NLD",
    "Belgium": "BEL",
    "Sweden": "SWE",
    "Switzerland": "CHE",
    "Norway": "NOR",
    "Denmark": "DNK",
    "Austria": "AUT",
    "Finland": "FIN",
    "Ireland": "IRL",
    "New Zealand": "NZL",
    "Singapore": "SGP",
    "Hong Kong SAR": "HKG",
    "Israel": "ISR",
    "Korea": "KOR",
    "Portugal": "PRT",
    "Greece": "GRC",
    "Czech Republic": "CZE",
    "Slovak Republic": "SVK",
    "Slovenia": "SVN",
    "Estonia": "EST",
    "Latvia": "LVA",
    "Lithuania": "LTU",
    "Cyprus": "CYP",
    "Malta": "MLT",
    "Iceland": "ISL",
    "Luxembourg": "LUX",
    "China": "CHN",
    "India": "IND",
    "Brazil": "BRA",
    "Russia": "RUS",
    "Mexico": "MEX",
    "Indonesia": "IDN",
    "Turkey": "TUR",
    "Saudi Arabia": "SAU",
    "Argentina": "ARG",
    "South Africa": "ZAF",
    "Thailand": "THA",
    "Malaysia": "MYS",
    "Philippines": "PHL",
    "Poland": "POL",
    "Egypt": "EGY",
    "Pakistan": "PAK",
    "Vietnam": "VNM",
    "Bangladesh": "BGD",
    "Nigeria": "NGA",
    "Iraq": "IRQ",
    "Colombia": "COL",
    "Chile": "CHL",
    "Romania": "ROU",
    "Peru": "PER",
    "Ukraine": "UKR",
    "Morocco": "MAR",
    "Kazakhstan": "KAZ",
    "Qatar": "QAT",
    "United Arab Emirates": "ARE",
    "Kuwait": "KWT",
    "Hungary": "HUN",
    "Algeria": "DZA",
    "Oman": "OMN",
    "Croatia": "HRV",
    "Belarus": "BLR",
    "Bulgaria": "BGR",
}


def country_name_to_iso3(
    country_name: str | float | None,
    *,
    mapping: Mapping[str, str] = COUNTRY_NAME_TO_CODE,
) -> str | None:
    """Best-effort mapping from country display name to ISO3 code.

    If `country_name` is already an ISO-like code, the notebook logic treated it as-is.
    We keep the same behavior here by returning `country_name` when not found.
    """

    if country_name is None or pd.isna(country_name):
        return None

    if not isinstance(country_name, str):
        country_name = str(country_name)
    country_name = country_name.strip()

    return mapping.get(country_name, country_name)


def classify_income_group_from_code(
    code: str | float | None,
    *,
    ae_codes: Collection[str] = AE_COUNTRY_CODES,
    em_codes: Collection[str] = EM_COUNTRY_CODES,
    other_label: str = "LC",
    unknown_label: str = "Unknown",
) -> str:
    """Classify a country ISO3 code into income groups.

    Default groups follow the notebook convention:
    - AE: advanced economies
    - EM: emerging markets
    - LC: everything else (lower/other bucket)
    """

    if code is None or pd.isna(code):
        return unknown_label

    code_str = str(code).strip()
    if code_str in ae_codes:
        return "AE"
    if code_str in em_codes:
        return "EM"
    return other_label


def classify_income_group_from_country_name(
    country_name: str | float | None,
    *,
    ae_codes: Collection[str] = AE_COUNTRY_CODES,
    em_codes: Collection[str] = EM_COUNTRY_CODES,
    other_label: str = "LIC",
    null_label: str = "LIC",
    name_to_code: Mapping[str, str] = COUNTRY_NAME_TO_CODE,
) -> str:
    """Notebook-style classification from country name to income groups.

    This mirrors `classify_income_group_v2` in `data_vis.ipynb`:
    - missing name -> `null_label`
    - AE/EM based on ISO code lists
    - otherwise -> `other_label` (notebook used 'LIC')
    """

    code = country_name_to_iso3(country_name, mapping=name_to_code)
    if code is None:
        return null_label

    if code in ae_codes:
        return "AE"
    if code in em_codes:
        return "EM"
    return other_label


# ----------------------------
# DataFrame utilities
# ----------------------------

def _require_columns(df: pd.DataFrame, cols: Sequence[str], *, context: str = "") -> None:
    """Raise a readable error if required columns are missing."""

    missing = [c for c in cols if c not in df.columns]
    if missing:
        ctx = f" ({context})" if context else ""
        raise ValueError(f"Missing required columns{ctx}: {missing}. Available: {list(df.columns)}")


def coerce_year_int(df: pd.DataFrame, *, year_col: str = "year") -> pd.DataFrame:
    """Return a copy with `year_col` coerced to pandas nullable integer."""

    out = df.copy()
    if year_col in out.columns:
        out[year_col] = pd.to_numeric(out[year_col], errors="coerce").astype("Int64")
    return out


def filter_year_range(
    df: pd.DataFrame,
    *,
    year_col: str = "year",
    start_year: int = 2015,
    end_year: int = 2023,
    dropna_year: bool = True,
) -> pd.DataFrame:
    """Filter rows to an inclusive year range."""

    _require_columns(df, [year_col], context="filter_year_range")
    out = coerce_year_int(df, year_col=year_col)
    if dropna_year:
        out = out[out[year_col].notna()].copy()

    out = out[(out[year_col] >= start_year) & (out[year_col] <= end_year)].copy()
    out[year_col] = out[year_col].astype(int)
    return out


def compute_year_group_counts(
    df: pd.DataFrame,
    *,
    year_col: str,
    group_col: str,
    group_order: Sequence[str] | None = None,
    fill_value: int = 0,
) -> pd.DataFrame:
    """Return a year x group count table."""

    _require_columns(df, [year_col, group_col], context="compute_year_group_counts")
    counts = df.groupby([year_col, group_col]).size().unstack(fill_value=fill_value)
    if group_order is not None:
        for g in group_order:
            if g not in counts.columns:
                counts[g] = fill_value
        counts = counts[list(group_order)]
    return counts


# ----------------------------
# Plot styling helpers
# ----------------------------


def style_axes(
    ax: Any,
    *,
    facecolor: str = "#F0F0F0",
    grid: bool = True,
    grid_axis: str = "y",
    grid_alpha: float = 0.3,
    grid_linestyle: str = "-",
    grid_linewidth: float = 0.5,
) -> None:
    """Apply the recurring chart styling used in the notebook."""

    ax.set_axisbelow(True)
    ax.set_facecolor(facecolor)
    if grid:
        ax.grid(True, axis=grid_axis, alpha=grid_alpha, linestyle=grid_linestyle, linewidth=grid_linewidth)


# ----------------------------
# Plot: stacked bars (counts)
# ----------------------------


def plot_stacked_counts_by_year(
    counts: pd.DataFrame,
    *,
    group_order: Sequence[str],
    colors: Mapping[str, str] | None = None,
    title: str = "Number of Article IV Reports by Year-Income Group",
    xlabel: str = "Year",
    ylabel: str = "Number of Reports",
    width: float = 0.5,
    ax: Any = None,
) -> Any:
    """Stacked count bars by year.

    Parameters
    - counts: DataFrame indexed by year with group columns
    - group_order: plotting order of groups
    """

    import matplotlib.pyplot as plt  # type: ignore[import-not-found]  # local import for notebook friendliness

    if colors is None:
        colors = {"AE": "#2E5C8A", "EM": "#8EBDD6", "LC": "#2C9D5F", "LIC": "#2C9D5F"}

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))

    years = counts.index
    bottom = np.zeros(len(years), dtype=float)

    for g in group_order:
        vals = counts[g].to_numpy()
        ax.bar(years, vals, width, label=g, bottom=bottom, color=colors.get(g, "#999999"))
        bottom += vals

    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(loc="upper right")
    ax.set_xticks(years)
    ax.set_xticklabels(years, rotation=0)
    style_axes(ax, grid=True, grid_axis="y", grid_linestyle="--")

    plt.tight_layout()
    return ax


# ----------------------------
# Agreement: "no disagreement" proportions
# ----------------------------


def add_no_disagreement_flag(
    df: pd.DataFrame,
    *,
    agreement_col: str = "agreement",
    disagreement_value: str = "disagreement exists",
    out_col: str = "no_disagreement",
) -> pd.DataFrame:
    """Add a 0/1 indicator for rows without disagreement."""

    _require_columns(df, [agreement_col], context="add_no_disagreement_flag")
    out = df.copy()
    out[out_col] = out[agreement_col].apply(lambda x: 1 if x != disagreement_value else 0)
    return out


def compute_no_disagreement_proportions_by_year(
    df: pd.DataFrame,
    *,
    year_col: str = "year",
    flag_col: str = "no_disagreement",
    group_col: str = "income_group",
    groups: Sequence[str] = ("ALL", "AE", "EM", "LIC"),
) -> pd.DataFrame:
    """Compute percent of reports without disagreement (ALL + by group) per year."""

    _require_columns(df, [year_col, flag_col, group_col], context="compute_no_disagreement_proportions_by_year")
    proportions: dict[str, dict[int, float]] = {}

    all_by_year = df.groupby(year_col)[flag_col].agg(["sum", "count"])
    proportions["ALL"] = (all_by_year["sum"] / all_by_year["count"] * 100).to_dict()  # type: ignore[assignment]

    for g in [x for x in groups if x != "ALL"]:
        sub = df[df[group_col] == g]
        by_year = sub.groupby(year_col)[flag_col].agg(["sum", "count"])
        proportions[g] = (by_year["sum"] / by_year["count"] * 100).to_dict()  # type: ignore[assignment]

    years = sorted(pd.unique(df[year_col].dropna()).tolist())
    out = pd.DataFrame(index=years)
    for g in groups:
        out[g] = [proportions.get(g, {}).get(int(y), np.nan) for y in years]

    return out


def plot_group_lines_by_year(
    df: pd.DataFrame,
    *,
    groups: Sequence[str],
    colors: Mapping[str, str] | None = None,
    title: str = "Proportion of Countries without Sector Disagreement",
    xlabel: str = "Year",
    ylabel: str = "Proportion (%)",
    ylim: tuple[float, float] | None = (30, 105),
    ax: Any = None,
) -> Any:
    """Multi-line plot for group series over year index."""

    import matplotlib.pyplot as plt  # type: ignore[import-not-found]

    if colors is None:
        colors = {
            "ALL": "#E74C3C",
            "AE": "#1F4788",
            "EM": "#7DC8E8",
            "LIC": "#27AE60",
            "LC": "#27AE60",
        }

    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 7))

    for g in groups:
        ax.plot(
            df.index,
            df[g],
            marker="o",
            linewidth=2.5,
            markersize=6,
            label=g,
            color=colors.get(g, "#333333"),
        )

    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
    ax.legend(loc="upper left", fontsize=11, frameon=True)
    ax.set_xticks(df.index)
    ax.set_xticklabels(df.index, rotation=0)
    if ylim is not None:
        ax.set_ylim(*ylim)

    style_axes(ax, grid=True, grid_axis="both")
    plt.tight_layout()
    return ax


# ----------------------------
# Disagreement areas: categorization
# ----------------------------


def extract_categories_from_text(
    text: str | float | None,
    *,
    categories: Mapping[str, Sequence[str]],
) -> list[str]:
    """Extract all categories whose keyword list matches the text."""

    if text is None or pd.isna(text):
        return []

    text_lower = str(text).lower()
    found: list[str] = []

    for category, keywords in categories.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                found.append(category)
                break

    return found


def add_extracted_categories(
    df: pd.DataFrame,
    *,
    text_col: str,
    categories: Mapping[str, Sequence[str]],
    out_col: str = "categories",
) -> pd.DataFrame:
    """Add a list-valued `out_col` containing extracted categories."""

    _require_columns(df, [text_col], context="add_extracted_categories")
    out = df.copy()
    out[out_col] = out[text_col].apply(lambda x: extract_categories_from_text(x, categories=categories))
    return out


def explode_categories(
    df: pd.DataFrame,
    *,
    categories_col: str = "categories",
    min_len: int = 1,
) -> pd.DataFrame:
    """Keep rows with >= `min_len` categories and explode to long format."""

    _require_columns(df, [categories_col], context="explode_categories")
    out = df[df[categories_col].apply(lambda x: isinstance(x, list) and len(x) >= min_len)].copy()
    return out.explode(categories_col)


def compute_category_percentage_by_year(
    df_long: pd.DataFrame,
    *,
    total_reports_by_year: pd.Series,
    year_col: str = "year",
    category_col: str = "categories",
    category_order: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Compute (% of reports) with disagreement by category per year."""

    _require_columns(df_long, [year_col, category_col], context="compute_category_percentage_by_year")
    disagree_counts = df_long.groupby([year_col, category_col]).size().unstack(fill_value=0)
    # Ensure we include all years from the denominator series, with 0 disagreement counts when missing.
    disagree_counts = disagree_counts.reindex(total_reports_by_year.index, fill_value=0)
    disagree_pct = (disagree_counts.div(total_reports_by_year, axis=0) * 100).round(2).fillna(0.0)

    if category_order is not None:
        for c in category_order:
            if c not in disagree_pct.columns:
                disagree_pct[c] = 0.0
        disagree_pct = disagree_pct[list(category_order)]

    return disagree_pct


def plot_category_trends(
    disagree_pct: pd.DataFrame,
    *,
    categories: Sequence[str],
    colors: Mapping[str, str] | None = None,
    title: str = "% of Reports with Disagreement by Area",
    xlabel: str = "Year",
    ylabel: str = "% of Reports",
    ax: Any = None,
) -> Any:
    """Multi-line plot for category percentages."""

    import matplotlib.pyplot as plt  # type: ignore[import-not-found]

    if colors is None:
        colors = {}

    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 7))

    years_plot = disagree_pct.index
    for cat in categories:
        ax.plot(
            years_plot,
            disagree_pct[cat],
            marker="o",
            linewidth=2,
            markersize=5,
            label=cat,
            color=colors.get(cat, "#333333"),
        )

    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
    ax.legend(loc="upper right", fontsize=9, frameon=True, ncol=1)
    ax.set_xticks(years_plot)
    ax.set_xticklabels(years_plot, rotation=0)
    ax.set_ylim(bottom=0)

    style_axes(ax, grid=True, grid_axis="both")
    plt.tight_layout()
    return ax


# ----------------------------
# Stance: wide pivot + IMF vs authority comparison
# ----------------------------


def pivot_stance_wide(
    df: pd.DataFrame,
    *,
    id_cols: Sequence[str] = ("Print ISBN", "topic", "country", "year"),
    author_col: str = "TEXT_AUTHOR",
    stance_cols: Sequence[str] = ("stance_current", "stance_future"),
    author_map: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """Pivot stance rows to wide: <author_prefix>_<stance_col>."""

    df = df.copy()
    _require_columns(df, [author_col], context="pivot_stance_wide")

    if author_map is None:
        author_map = {
            "IMF staff": "imf_staff",
            "country authority": "country_authority",
        }

    def _prefix(x: str | None) -> str:
        x = (x or "").strip()
        if x in author_map:
            return author_map[x]
        x = x.lower()
        x = re.sub(r"\s+", "_", x)
        x = re.sub(r"[^a-z0-9_]+", "_", x)
        x = re.sub(r"_+", "_", x).strip("_")
        return x or "unknown"

    id_cols_found = [c for c in id_cols if c in df.columns]
    if not id_cols_found:
        raise ValueError(f"No id columns found. Available columns: {list(df.columns)}")

    stance_cols_found = [c for c in stance_cols if c in df.columns]
    if not stance_cols_found:
        raise ValueError(f"No stance columns found. Available columns: {list(df.columns)}")

    df["_author_prefix"] = df[author_col].apply(_prefix)

    wide = df.pivot_table(index=id_cols_found, columns="_author_prefix", values=stance_cols_found, aggfunc="first")
    wide.columns = [f"{author}_{stance}" for stance, author in wide.columns]
    return wide.reset_index()


STANCE_DIRECTION_SCORE_DEFAULT: dict[str, int] = {
    "loosening": -2,
    "loosening bias": -1,
    "no change": 0,
    "tightening bias": 1,
    "tightening": 2,
}


def bucket_imf_vs_auth_diff(d: float) -> str:
    """Default bucketing logic from the notebook (IMF score - authority score)."""

    if d >= 3:
        return "significantly tighter"
    if d == 2:
        return "tighter"
    if d == 1:
        return "moderately tighter"
    if d == 0:
        return "same"
    if d == -1:
        return "moderately looser"
    return "looser"  # d <= -2


DEFAULT_IMF_VS_AUTH_ORDER: tuple[str, ...] = (
    "significantly tighter",
    "tighter",
    "moderately tighter",
    "same",
    "moderately looser",
    "looser",
)


def compute_imf_vs_authority_share(
    df_wide: pd.DataFrame,
    *,
    year_col: str = "year",
    imf_col: str,
    auth_col: str,
    direction_score: Mapping[str, int] = STANCE_DIRECTION_SCORE_DEFAULT,
    bucket_func: Callable[[float], str] = bucket_imf_vs_auth_diff,
    order: Sequence[str] = DEFAULT_IMF_VS_AUTH_ORDER,
    start_year: int = 2015,
    end_year: int = 2023,
) -> pd.DataFrame:
    """Compute a year x bucket share table (rows sum to 1)."""

    df = filter_year_range(df_wide, year_col=year_col, start_year=start_year, end_year=end_year)

    if imf_col not in df.columns or auth_col not in df.columns:
        raise ValueError(
            f"Expected columns '{imf_col}' and '{auth_col}'. Available: {list(df.columns)}"
        )

    plot_df = df.copy()
    plot_df["imf_score"] = plot_df[imf_col].map(direction_score)
    plot_df["auth_score"] = plot_df[auth_col].map(direction_score)
    plot_df = plot_df[plot_df["imf_score"].notna() & plot_df["auth_score"].notna()].copy()

    plot_df["diff"] = plot_df["imf_score"] - plot_df["auth_score"]
    plot_df["imf_vs_auth"] = plot_df["diff"].apply(bucket_func)

    share = plot_df.groupby([year_col, "imf_vs_auth"]).size().unstack(fill_value=0)
    for cat in order:
        if cat not in share.columns:
            share[cat] = 0
    share = share[list(order)]
    share = share.div(share.sum(axis=1), axis=0).fillna(0.0)

    return share


def plot_stacked_proportions_by_year(
    share: pd.DataFrame,
    *,
    order: Sequence[str] = DEFAULT_IMF_VS_AUTH_ORDER,
    colors: Mapping[str, str] | None = None,
    title: str = "IMF Advice Compared to Authorities' Policy Direction",
    xlabel: str = "Year",
    ax: Any = None,
    xtick_rotation: int = 90,
) -> Any:
    """Stacked proportion bars (shares) by year."""

    import matplotlib.pyplot as plt  # type: ignore[import-not-found]

    if colors is None:
        colors = {
            "significantly tighter": "#1f77b4",
            "tighter": "#4aa3df",
            "moderately tighter": "#bcdff5",
            "same": "#f2f2f2",
            "moderately looser": "#f7c6ae",
            "looser": "#e76f51",
        }

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))

    bottom = np.zeros(len(share), dtype=float)
    x = share.index.to_list()

    for cat in order:
        vals = share[cat].to_numpy()
        ax.bar(x, vals, bottom=bottom, label=cat, color=colors.get(cat, "#999999"), edgecolor="none")
        bottom += vals

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("")
    ax.set_ylim(0, 1.0)
    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in x], rotation=xtick_rotation)
    style_axes(ax, grid=True, grid_axis="y")
    ax.legend(loc="upper right", frameon=True)

    plt.tight_layout()
    return ax
