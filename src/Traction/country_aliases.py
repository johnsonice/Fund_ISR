"""Canonical normalization for non-standard / legacy country codes.

The Article IV pipeline historically emitted a handful of country codes that do
NOT exist as `ISO3` rows in `docs/reference/country_meta_info.xlsx`. When those
codes reach the `Primary Country Code -> ISO3` left-join in
`post_estimate_analysis/final_dataset_utils.py`, the join silently yields a NaN
`country` (and NaN income group), and the rows show up as "missing country" in
the final / merged core datasets.

This module is the single source of truth for fixing that. It maps each
non-standard code to the reference ISO3 it should have been, so both pipelines
(main via `create_final_dataset.py`, incremental via step 02 / 07b) resolve to a
code the reference actually carries.

All targets here are verified to exist in `country_meta_info.xlsx` (`ISO3`
column). Keep this list in sync with that reference: if a target code is ever
removed from the reference, the join will break again.
"""

from __future__ import annotations

from typing import Any

# Legacy / non-standard code  ->  canonical reference ISO3.
#
# Rationale per entry (titles confirmed from main_base/df_aiv.csv):
#   UVK -> KOS   Old Kosovo code; reference uses KOS ("Republic of Kosovo" reports).
#   XKX -> KOS   Alternate Kosovo code variant.
#   EUR -> G163  Euro Area; reference's Euro Area row is ISO3 "G163".
#   EMU -> G163  Alternate Euro-area label.
#   ANT -> CUW   "Kingdom of the Netherlands—Curaçao and Sint Maarten" reports;
#                Netherlands Antilles dissolved 2010. Map to Curaçao (CUW), the
#                primary named territory; reference also carries SXM separately.
#   CEE -> SVN   Mislabeled "Republic of Slovenia" report (the CEE code was wrong).
CODE_ALIASES: dict[str, str] = {
    "UVK": "KOS",
    "XKX": "KOS",
    "EUR": "G163",
    "EMU": "G163",
    "ANT": "CUW",
    "CEE": "SVN",
}


def normalize_country_code(value: Any) -> Any:
    """Return the canonical reference ISO3 for a possibly-legacy country code.

    Non-string / NaN inputs are returned unchanged so callers can apply this
    element-wise without first dropping nulls. Matching is case-insensitive and
    whitespace-tolerant; unknown codes pass through untouched (only the explicit
    legacy aliases above are rewritten).
    """
    if not isinstance(value, str):
        return value
    key = value.strip().upper()
    return CODE_ALIASES.get(key, value)
