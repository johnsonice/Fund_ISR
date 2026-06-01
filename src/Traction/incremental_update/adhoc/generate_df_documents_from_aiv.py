"""Generate df_documents_incremental.csv from an existing df_aiv_incremental.csv.

Adhoc / one-off helper: rebuilds the legacy-schema per-document text rollup
(`df_documents_incremental.csv`) from an already-written `df_aiv_incremental.csv`,
without re-running XML extraction. Useful when step 03 was run before the
documents-rollup output was added.

The output matches the legacy `df_documents.csv` schema produced by
`temp/reference_code/2.topic_type_classification.py` lines 207-234:
    index, Print ISBN, staff, buff, country, year, publication_date

Usage:
    python generate_df_documents_from_aiv.py \
        --aiv-csv /path/to/df_aiv_incremental.csv \
        [--output-csv /path/to/df_documents_incremental.csv]

If --output-csv is omitted, writes alongside the input as
`df_documents_incremental.csv`.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd


def _parse_paragraphs(value: Any) -> list[str]:
    """Parse a paragraph-list cell back into a Python list.

    `df_aiv_incremental.csv` stores list columns as JSON strings (see
    `_serialize_for_csv` in 03_incremental_aiv_update.py). NaN / empty cells
    become an empty list.
    """
    if value is None:
        return []
    if isinstance(value, float) and pd.isna(value):
        return []
    if isinstance(value, list):
        return value
    if not isinstance(value, str) or value == "":
        return []
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _join_paragraphs(value: Any) -> str:
    return "\n".join(_parse_paragraphs(value))


def build_documents_df(df_aiv: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in df_aiv.iterrows():
        staff = _join_paragraphs(r.get("paragraphs_sr")) + "\n" + _join_paragraphs(r.get("paragraphs_sa"))
        buff = _join_paragraphs(r.get("paragraphs_av")) + "\n" + _join_paragraphs(r.get("paragraphs_bu"))
        country = r.get("Primary Country Description")
        if not isinstance(country, str) or country == "":
            country = r.get("countries")
        rows.append(
            {
                "Print ISBN": r["Print ISBN"],
                "staff": staff,
                "buff": buff,
                "country": country,
                "year": r.get("Year from title"),
                "publication_date": r.get("Publication Date"),
            }
        )
    return pd.DataFrame(rows).reset_index()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--aiv-csv", type=Path, required=True, help="Path to existing df_aiv_incremental.csv")
    parser.add_argument("--output-csv", type=Path, default=None, help="Destination CSV (default: df_documents_incremental.csv alongside input)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    aiv_csv = args.aiv_csv.resolve()
    output_csv = (args.output_csv or aiv_csv.parent / "df_documents_incremental.csv").resolve()

    df_aiv = pd.read_csv(aiv_csv)
    df_documents = build_documents_df(df_aiv)

    df_documents.to_csv(
        output_csv,
        index=False,
        encoding="utf-8-sig",
        quoting=csv.QUOTE_ALL,
        lineterminator="\n",
    )

    print(f"Read {len(df_aiv)} rows from {aiv_csv}")
    print(f"Wrote {len(df_documents)} rows to {output_csv}")


if __name__ == "__main__":
    main()
