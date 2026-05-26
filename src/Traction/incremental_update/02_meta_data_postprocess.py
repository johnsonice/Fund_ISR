from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import pandas as pd

try:
    import config
except ModuleNotFoundError:  # pragma: no cover
    import sys

    _TRACTION_DIR = Path(__file__).resolve().parent.parent
    if str(_TRACTION_DIR) not in sys.path:
        sys.path.insert(0, str(_TRACTION_DIR))
    import config  # type: ignore  # noqa: E402

YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")
ARTICLE_IV_PATTERN = re.compile(r"article\s*iv", re.IGNORECASE)
DEFAULT_INPUT_PATH = config.output_dir / "incremental_update" / "spr_isr_com_articleiv_2025_metadata.xlsx"
DEFAULT_OUTPUT_PATH = config.output_dir / "incremental_update" / "spr_isr_com_articleiv_2025_metadata_postprocessed.xlsx"
DEFAULT_COUNTRY_REFERENCE_PATH = (
    Path(__file__).resolve().parent.parent / "docs" / "reference" / "country_meta_info.xlsx"
)
FILTERED_SHEET_COLUMNS = [
    "package_folder",
    "package_path",
    "title_full",
    "Country Name from title",
    "Primary Country Code",
    "Primary Country Description",
    "Year from title",
    "AIV",
    "publication_date",
    "publication_time",
    "publication_day",
    "publication_month",
    "publication_year",
    "document_type",
    "document_type_code",
    "language",
    "series_name",
    "countries",
    "country_codes",
    "regions",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Postprocess generated XML metadata workbooks with title-derived fields."
    )
    parser.add_argument(
        "--input-path",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help=f"Path to the generated metadata Excel workbook. Default: {DEFAULT_INPUT_PATH}",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path to write the postprocessed workbook. Default: {DEFAULT_OUTPUT_PATH}",
    )
    parser.add_argument(
        "--country-reference-path",
        type=Path,
        default=DEFAULT_COUNTRY_REFERENCE_PATH,
        help=f"Path to the country reference workbook. Default: {DEFAULT_COUNTRY_REFERENCE_PATH}",
    )
    return parser.parse_args(argv)


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _normalize_country_name(value: str) -> str:
    value = _clean_text(value).casefold()
    value = re.sub(r"\s+", " ", value)
    return value


def _country_aliases(country_name: str) -> set[str]:
    country_name = _clean_text(country_name)
    if not country_name:
        return set()

    aliases = {_normalize_country_name(country_name)}
    normalized = _normalize_country_name(country_name)
    if normalized.startswith("the "):
        aliases.add(normalized[4:])
    else:
        aliases.add(f"the {normalized}")
    if "," in country_name:
        parts = [part.strip() for part in country_name.split(",") if part.strip()]
        if len(parts) >= 2:
            aliases.add(_normalize_country_name(" ".join(parts[1:] + [parts[0]])))
    return aliases


def load_country_reference(country_reference_path: Path) -> dict[str, tuple[str, str]]:
    df_ref = pd.read_excel(country_reference_path)
    required_cols = {"Country", "ISO3"}
    missing_cols = required_cols - set(df_ref.columns)
    if missing_cols:
        raise ValueError(
            f"Country reference workbook must contain columns {sorted(required_cols)}; missing {sorted(missing_cols)}"
        )

    lookup: dict[str, tuple[str, str]] = {}
    name_columns = [col for col in ["Country", "Country.1"] if col in df_ref.columns]
    for _, row in df_ref.iterrows():
        canonical_country = _clean_text(row.get("Country", ""))
        iso3 = _clean_text(row.get("ISO3", ""))
        if not canonical_country:
            continue
        for name_col in name_columns:
            country_name = _clean_text(row.get(name_col, ""))
            if not country_name:
                continue
            for alias in _country_aliases(country_name):
                lookup.setdefault(alias, (canonical_country, iso3))
    return lookup


def resolve_primary_country(country_name_from_title: str, country_lookup: dict[str, tuple[str, str]]) -> tuple[str, str]:
    for alias in _country_aliases(country_name_from_title):
        if alias in country_lookup:
            canonical_country, iso3 = country_lookup[alias]
            return iso3, canonical_country
    return "", ""


def _extract_title_prefix(title_full: str) -> str:
    title_full = _clean_text(title_full)
    if ":" not in title_full:
        return ""
    return _clean_text(title_full.split(":", 1)[0])


def extract_year_from_title(title_full: str) -> int | None:
    match = YEAR_PATTERN.search(_clean_text(title_full))
    if not match:
        return None
    return int(match.group(0))


def has_article_iv(title_full: str) -> bool:
    return bool(ARTICLE_IV_PATTERN.search(_clean_text(title_full)))


def extract_country_name_from_title(title_full: str, countries: str = "") -> str:
    prefix = _extract_title_prefix(title_full)
    if not prefix:
        return ""

    country_values = [_clean_text(value) for value in _clean_text(countries).split(" | ") if _clean_text(value)]
    if country_values:
        normalized_prefix = _normalize_country_name(prefix)
        for country_value in country_values:
            if normalized_prefix in _country_aliases(country_value):
                return prefix

    if has_article_iv(title_full):
        return prefix
    return ""


def build_postprocessed_metadata(
    df: pd.DataFrame,
    country_lookup: dict[str, tuple[str, str]],
) -> pd.DataFrame:
    df = df.copy()
    if "title_full" not in df.columns:
        raise ValueError("Input workbook metadata sheet must contain a 'title_full' column")

    if "countries" not in df.columns:
        df["countries"] = ""

    df["Country Name from title"] = df.apply(
        lambda row: extract_country_name_from_title(
            title_full=row.get("title_full", ""),
            countries=row.get("countries", ""),
        ),
        axis=1,
    )
    primary_country = df["Country Name from title"].apply(lambda value: resolve_primary_country(value, country_lookup))
    df["Primary Country Code"] = [iso3 for iso3, _ in primary_country]
    df["Primary Country Description"] = [country for _, country in primary_country]
    df["Year from title"] = df["title_full"].apply(extract_year_from_title).astype("Int64")
    df["AIV"] = df["title_full"].apply(has_article_iv)
    return df


def build_filtered_sheet(df: pd.DataFrame) -> pd.DataFrame:
    filtered_df = df[df["AIV"] == True].copy()
    for column in FILTERED_SHEET_COLUMNS:
        if column not in filtered_df.columns:
            filtered_df[column] = pd.NA

    filtered_df = filtered_df[FILTERED_SHEET_COLUMNS]
    filtered_df = filtered_df.rename(columns={"package_folder": "Print ISBN"})
    return filtered_df


def _autofit_worksheet_columns(worksheet: Any) -> None:
    for column_cells in worksheet.columns:
        values = [str(cell.value) for cell in column_cells if cell.value is not None]
        if not values:
            continue
        max_length = min(max(len(value) for value in values) + 2, 80)
        worksheet.column_dimensions[column_cells[0].column_letter].width = max_length


def resolve_output_path(input_path: Path, output_path: Path | None) -> Path:
    if output_path is not None:
        return output_path
    return input_path.with_name(f"{input_path.stem}_postprocessed{input_path.suffix}")


def write_postprocessed_workbook(
    df: pd.DataFrame,
    input_path: Path,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_df = build_filtered_sheet(df)

    try:
        summary_df = pd.read_excel(input_path, sheet_name="summary")
    except ValueError:
        summary_df = pd.DataFrame(columns=["metric", "value"])

    derived_summary = pd.DataFrame(
        [
            {"metric": "postprocess_input", "value": str(input_path)},
            {"metric": "rows", "value": len(df)},
            {"metric": "aiv_true_count", "value": int(df["AIV"].sum())},
            {
                "metric": "country_name_from_title_nonempty",
                "value": int((df["Country Name from title"].fillna("").astype(str).str.strip() != "").sum()),
            },
            {
                "metric": "year_from_title_nonnull",
                "value": int(df["Year from title"].notna().sum()),
            },
            {
                "metric": "filtered_sheet_rows",
                "value": len(filtered_df),
            },
        ]
    )

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="metadata")
        filtered_df.to_excel(writer, index=False, sheet_name="filtered_sheet")
        summary_df.to_excel(writer, index=False, sheet_name="summary")
        derived_summary.to_excel(writer, index=False, sheet_name="postprocess_summary")

        for sheet_name in writer.book.sheetnames:
            worksheet = writer.book[sheet_name]
            worksheet.freeze_panes = "A2"
            _autofit_worksheet_columns(worksheet)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    input_path = args.input_path.resolve()
    output_path = resolve_output_path(input_path, args.output_path).resolve()
    country_reference_path = args.country_reference_path.resolve()

    df = pd.read_excel(input_path, sheet_name="metadata")
    country_lookup = load_country_reference(country_reference_path)
    postprocessed_df = build_postprocessed_metadata(df, country_lookup=country_lookup)
    write_postprocessed_workbook(postprocessed_df, input_path=input_path, output_path=output_path)
    print(f"Wrote postprocessed metadata workbook to {output_path}")


if __name__ == "__main__":
    main()
