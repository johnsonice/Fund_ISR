from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

_THIS_DIR = Path(__file__).resolve().parent
_TRACTION_DIR = _THIS_DIR.parent
if str(_TRACTION_DIR) not in sys.path:
    sys.path.insert(0, str(_TRACTION_DIR))

import config  # noqa: E402

# Reuse format-agnostic helpers from the XML sibling. The sibling's filename
# starts with a digit, so import it dynamically via importlib.
import importlib.util as _ilu

_XML_SCRIPT = _THIS_DIR / "01_data_preprocess_incremental.py"
_spec = _ilu.spec_from_file_location("_xml_pipeline", _XML_SCRIPT)
_xml_pipeline = _ilu.module_from_spec(_spec)  # type: ignore[arg-type]
assert _spec and _spec.loader
_spec.loader.exec_module(_xml_pipeline)  # type: ignore[union-attr]

SINGLE_FIELDS = _xml_pipeline.SINGLE_FIELDS
LIST_FIELDS = _xml_pipeline.LIST_FIELDS
MONTH_LOOKUP = _xml_pipeline.MONTH_LOOKUP
_clean_text = _xml_pipeline._clean_text
_join_unique = _xml_pipeline._join_unique
_split_title_and_subtitle = _xml_pipeline._split_title_and_subtitle
_autofit_worksheet_columns = _xml_pipeline._autofit_worksheet_columns
resolve_output_path = _xml_pipeline.resolve_output_path
discover_packages = _xml_pipeline.discover_packages
TITLE_DECORATION_PATTERN = re.compile(
    r"\s+in:\s+IMF Staff Country Reports Volume\s+\d+\s+Issue\s+\d+\s*\(\d{4}\)\s*$",
    re.IGNORECASE,
)
TITLE_LEADING_VOLUME_PATTERN = re.compile(
    r"^IMF Staff Country Reports Volume\s+\d+\s+Issue\s+\d+:\s*", re.IGNORECASE
)
TITLE_TRAILING_YEAR_PATTERN = re.compile(r"\s*\(\d{4}\)\s*$")

DATA_LAYER_PATTERN = re.compile(r"dataLayer\.push\(\{(.+?)\}\)", re.DOTALL)
PF_KV_PATTERN = re.compile(r'"(pf:[A-Za-z]+)"\s*:\s*"((?:[^"\\]|\\.)*)"')
HTML_LANG_PATTERN = re.compile(r"<html[^>]*\blang\s*=\s*\"([^\"]+)\"", re.IGNORECASE)
HTML_DATA_LOCALE_PATTERN = re.compile(r"<html[^>]*\bdata-locale\s*=\s*\"([^\"]+)\"", re.IGNORECASE)
TITLE_PATTERN = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
CANONICAL_PATTERN = re.compile(
    r'<link\s+[^>]*\bhref\s*=\s*"([^"]+)"[^>]*\brel\s*=\s*"canonical"', re.IGNORECASE
)
CANONICAL_PATTERN_REV = re.compile(
    r'<link\s+[^>]*\brel\s*=\s*"canonical"[^>]*\bhref\s*=\s*"([^"]+)"', re.IGNORECASE
)
OG_DESCRIPTION_PATTERN = re.compile(
    r'<meta\s+[^>]*\bcontent\s*=\s*"([^"]+)"[^>]*\bproperty\s*=\s*"og:description"',
    re.IGNORECASE,
)
JOURNAL_URL_PATTERN = re.compile(
    r"journals/(\d+)/(\d{4})/(\d+)/", re.IGNORECASE
)
PUB_DATE_IN_DESCRIPTION = re.compile(
    r"published on\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", re.IGNORECASE
)
ISSUE_DATE_IN_DESCRIPTION = re.compile(
    r"Issue\s+\d+\s*\(([A-Za-z]+)\s+(\d{4})\)", re.IGNORECASE
)

MONTH_LOOKUP_EXT = {
    **MONTH_LOOKUP,
    **{name[:3]: code for name, code in MONTH_LOOKUP.items()},
    "sept": "09",
}

JS_STRING_ESCAPES = {
    r"\\\"": '"',
    r"\\'": "'",
    r"\\\\": "\\",
    r"\\/": "/",
    r"\\n": " ",
    r"\\r": " ",
    r"\\t": " ",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract publication-level metadata from rendered HTML package folders "
            "(IMF eLibrary 'imf_staff_reports_html_by_year_isbn' format) into the same "
            "Excel workbook schema as 01_data_preprocess_incremental.py."
        )
    )
    parser.add_argument(
        "--input-root",
        type=Path,
        required=True,
        help="Root directory whose direct subfolders are publication packages (one folder per ISBN).",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Output Excel workbook path. Defaults to config.output_dir/incremental_update/<input_root_name>_metadata.xlsx.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on the number of package folders to process, for testing.",
    )
    return parser.parse_args(argv)


_UNICODE_ESCAPE_PATTERN = re.compile(r"\\u([0-9a-fA-F]{4})")


def _unescape_js_string(value: str) -> str:
    value = _UNICODE_ESCAPE_PATTERN.sub(lambda m: chr(int(m.group(1), 16)), value)
    for token, repl in JS_STRING_ESCAPES.items():
        value = value.replace(token, repl)
    return value


def _extract_pf_metadata(html_text: str) -> dict[str, str]:
    block_match = DATA_LAYER_PATTERN.search(html_text)
    search_space = block_match.group(1) if block_match else html_text
    pf: dict[str, str] = {}
    for kv in PF_KV_PATTERN.finditer(search_space):
        key = kv.group(1)
        if key in pf:
            continue
        pf[key] = _unescape_js_string(kv.group(2))
    return pf


def _extract_html_head_fields(html_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}

    title_match = TITLE_PATTERN.search(html_text)
    if title_match:
        fields["html_title"] = _clean_text(title_match.group(1))

    canonical_match = CANONICAL_PATTERN.search(html_text) or CANONICAL_PATTERN_REV.search(html_text)
    if canonical_match:
        fields["canonical_url"] = _clean_text(canonical_match.group(1))

    og_match = OG_DESCRIPTION_PATTERN.search(html_text)
    if og_match:
        fields["og_description"] = _clean_text(og_match.group(1).replace("&quot;", '"'))

    lang_match = HTML_LANG_PATTERN.search(html_text)
    if lang_match:
        fields["html_lang"] = _clean_text(lang_match.group(1))
    if "html_lang" not in fields:
        locale_match = HTML_DATA_LOCALE_PATTERN.search(html_text)
        if locale_match:
            fields["html_lang"] = _clean_text(locale_match.group(1))

    return fields


def _strip_title_decoration(text: str) -> str:
    """Strip the eLibrary <title> tag decorations to leave a clean publication title.

    Examples:
        "Front Matter in: IMF Staff Country Reports Volume 2026 Issue 009 (2026)"
            -> "Front Matter"
        "IMF Staff Country Reports Volume 2026 Issue 009: Grenada: 2025 Article IV... (2026)"
            -> "Grenada: 2025 Article IV..."
    """
    cleaned = TITLE_DECORATION_PATTERN.sub("", text)
    cleaned = TITLE_LEADING_VOLUME_PATTERN.sub("", cleaned)
    cleaned = TITLE_TRAILING_YEAR_PATTERN.sub("", cleaned)
    return _clean_text(cleaned)


def _html_role(html_path: Path) -> str:
    name = html_path.name.lower()
    if name == "issue_toc.html":
        return "issue"
    article_match = re.match(r"article-a(\d{3})-[a-z]{2}\.html$", name)
    if article_match:
        article_number = int(article_match.group(1))
        if article_number == 0:
            return "front_matter"
        return f"article_{article_number:03d}"
    return "other"


def _html_priority(html_path: Path) -> tuple[int, int, str]:
    role = _html_role(html_path)
    if role == "issue":
        return (0, 0, html_path.name.lower())
    if role.startswith("article_"):
        return (1, int(role.split("_")[1]), html_path.name.lower())
    if role == "front_matter":
        return (2, 0, html_path.name.lower())
    return (3, 0, html_path.name.lower())


def discover_html_files(package_dir: Path) -> list[Path]:
    files = [p for p in package_dir.iterdir() if p.is_file() and p.suffix.lower() == ".html"]
    return sorted(files, key=_html_priority)


def _build_date_parts_from_description(og_description: str) -> dict[str, str]:
    if not og_description:
        return {}

    pub_match = PUB_DATE_IN_DESCRIPTION.search(og_description)
    if pub_match:
        day_raw, month_raw, year = pub_match.group(1), pub_match.group(2), pub_match.group(3)
        month = MONTH_LOOKUP_EXT.get(month_raw.lower(), "")
        day = day_raw.zfill(2)
        date = f"{year}-{month}-{day}" if month else f"{year}"
        return {
            "publication_date": date,
            "publication_day": day,
            "publication_month": month,
            "publication_year": year,
        }

    issue_match = ISSUE_DATE_IN_DESCRIPTION.search(og_description)
    if issue_match:
        month_raw, year = issue_match.group(1), issue_match.group(2)
        month = MONTH_LOOKUP_EXT.get(month_raw.lower(), "")
        date = f"{year}-{month}" if month else year
        return {
            "publication_date": date,
            "publication_day": "",
            "publication_month": month,
            "publication_year": year,
        }

    return {}


def _build_date_parts_from_canonical(canonical_url: str) -> dict[str, str]:
    if not canonical_url:
        return {}
    journal_match = JOURNAL_URL_PATTERN.search(canonical_url)
    if not journal_match:
        return {}
    return {
        "publication_year": journal_match.group(2),
    }


def _parse_volume_issue_from_canonical(canonical_url: str) -> dict[str, str]:
    if not canonical_url:
        return {"volume": "", "issue_number": ""}
    journal_match = JOURNAL_URL_PATTERN.search(canonical_url)
    if not journal_match:
        return {"volume": "", "issue_number": ""}
    return {
        "volume": journal_match.group(2),
        "issue_number": journal_match.group(3).lstrip("0") or "0",
    }


def parse_html_file(html_path: Path) -> dict[str, Any]:
    html_text = html_path.read_text(encoding="utf-8", errors="replace")
    pf = _extract_pf_metadata(html_text)
    head = _extract_html_head_fields(html_text)

    content_name = pf.get("pf:contentName", "")
    chunk_identifier = pf.get("pf:chunkIdentifier", "")
    content_category = pf.get("pf:contentCategory", "").lower()
    content_parent = pf.get("pf:contentParentName", "")
    title_parent_identifier = pf.get("pf:titleParentIdentifier", "")

    canonical_url = head.get("canonical_url", "")
    og_description = head.get("og_description", "")
    html_title_raw = head.get("html_title", "")

    title_full = content_name or _strip_title_decoration(html_title_raw)
    if not title_full and html_title_raw:
        title_full = _strip_title_decoration(html_title_raw)
    title, subtitle = _split_title_and_subtitle(title_full)

    date_parts: dict[str, str] = {
        "publication_date": "",
        "publication_time": "",
        "publication_day": "",
        "publication_month": "",
        "publication_year": "",
    }
    date_parts.update(_build_date_parts_from_canonical(canonical_url))
    date_parts.update({k: v for k, v in _build_date_parts_from_description(og_description).items() if v})

    vol_issue = _parse_volume_issue_from_canonical(canonical_url)

    if content_category == "nlm-journal-issue":
        document_type = "issue"
    elif content_category == "nlm-article":
        document_type = "article"
    else:
        document_type = ""

    return {
        "source_root_tag": content_category or "",
        "language": head.get("html_lang", ""),
        "document_type": document_type,
        "document_type_code": content_category,
        "title_full": title_full,
        "title": title,
        "subtitle": subtitle,
        "front_article_title": content_name if content_category == "nlm-article" else "",
        "issue_title": content_name if content_category == "nlm-journal-issue" else "",
        "book_title": "",
        "publication_title": content_parent,
        "journal_title": content_parent,
        "series_name": content_parent,
        "series_number": title_parent_identifier,
        "publisher_name": "International Monetary Fund",
        "publisher_location": "",
        "publication_date": date_parts.get("publication_date", ""),
        "publication_time": "",
        "publication_day": date_parts.get("publication_day", ""),
        "publication_month": date_parts.get("publication_month", ""),
        "publication_year": date_parts.get("publication_year", ""),
        "volume": vol_issue.get("volume", ""),
        "issue_number": vol_issue.get("issue_number", ""),
        "doi": chunk_identifier,
        "publisher_id": "",
        "translation_id": "",
        "stockcode": "",
        "repec": "",
        "docnumber": "",
        "ebook_isbn": "",
        "ppub_isbn": "",
        "epub_isbn": "",
        "pdf_isbn": "",
        "abstract": "",
        "elibrary_link": canonical_url,
        "elibrary_part_link": "",
        "prepared_by": "",
        "copyright_statement": "",
        "copyright_year": date_parts.get("publication_year", ""),
        "authors": "",
        "editors": "",
        "keywords": "",
        "country_codes": "",
        "countries": "",
        "regions": "",
        "topic_codes": "",
        "topics": "",
    }


def _empty_package_record(package_dir: Path, html_files: list[Path]) -> dict[str, Any]:
    record: dict[str, Any] = {
        "package_folder": package_dir.name,
        "package_path": str(package_dir),
        "xml_file_count": len(html_files),
        "parsed_xml_count": 0,
        "failed_xml_count": 0,
        "primary_source_xml": "",
        "primary_source_role": "",
        "title_source_xml": "",
        "publication_date_source_xml": "",
        "identifier_source_xml": "",
        "fallback_used": False,
        "parse_status": "not_started",
        "parse_notes": "",
        "xml_files": _join_unique(p.name for p in html_files),
        "xml_roles": _join_unique(_html_role(p) for p in html_files),
        "failed_xml_files": "",
    }
    for field in SINGLE_FIELDS:
        record[field] = ""
    for field in LIST_FIELDS - {"xml_files", "xml_roles", "failed_xml_files"}:
        record[field] = ""
    return record


TITLE_SOURCE_FIELDS = {
    "title_full", "title", "subtitle", "publication_title", "issue_title",
    "book_title", "front_article_title",
}
DATE_SOURCE_FIELDS = {
    "publication_date", "publication_time", "publication_day",
    "publication_month", "publication_year",
}
IDENTIFIER_SOURCE_FIELDS = {
    "doi", "publisher_id", "translation_id", "stockcode", "repec", "docnumber",
    "ebook_isbn", "ppub_isbn", "epub_isbn", "pdf_isbn",
}


def _merge_package_metadata(package_dir: Path) -> dict[str, Any]:
    html_files = discover_html_files(package_dir)
    record = _empty_package_record(package_dir, html_files)
    aggregate_lists: dict[str, list[str]] = {field: [] for field in LIST_FIELDS}
    parse_errors: list[str] = []

    for index, html_path in enumerate(html_files):
        try:
            html_metadata = parse_html_file(html_path)
        except Exception as exc:  # noqa: BLE001
            record["failed_xml_count"] += 1
            aggregate_lists["failed_xml_files"].append(html_path.name)
            parse_errors.append(f"{html_path.name}: {type(exc).__name__}: {exc}")
            continue

        # Skip the "Front Matter" article when picking a title — its contentName
        # is the publication title, but its document_type is "article" not "issue".
        # We still want it to count as parsed (it is valid HTML), just not as the
        # title source if a higher-priority issue file exists.
        role = _html_role(html_path)
        record["parsed_xml_count"] += 1
        if not record["primary_source_xml"]:
            record["primary_source_xml"] = html_path.name
            record["primary_source_role"] = role
            record["source_root_tag"] = html_metadata.get("source_root_tag", "")

        for field in LIST_FIELDS - {"xml_files", "xml_roles", "failed_xml_files"}:
            value = html_metadata.get(field, "")
            if value:
                aggregate_lists[field].extend(part for part in value.split(" | ") if part)

        for field in SINGLE_FIELDS:
            value = _clean_text(str(html_metadata.get(field, "")))
            if not value:
                continue
            if not record[field]:
                record[field] = value
                if index > 0:
                    record["fallback_used"] = True
                if field in TITLE_SOURCE_FIELDS and not record["title_source_xml"]:
                    record["title_source_xml"] = html_path.name
                if field in DATE_SOURCE_FIELDS and not record["publication_date_source_xml"]:
                    record["publication_date_source_xml"] = html_path.name
                if field in IDENTIFIER_SOURCE_FIELDS and not record["identifier_source_xml"]:
                    record["identifier_source_xml"] = html_path.name

    for field, values in aggregate_lists.items():
        joined = _join_unique(values)
        if joined:
            record[field] = joined

    if not record["title"] and record["title_full"]:
        record["title"], record["subtitle"] = _split_title_and_subtitle(record["title_full"])

    if not record["title_source_xml"] and record["primary_source_xml"] and record["title_full"]:
        record["title_source_xml"] = record["primary_source_xml"]
    if not record["publication_date_source_xml"] and record["primary_source_xml"] and record["publication_date"]:
        record["publication_date_source_xml"] = record["primary_source_xml"]
    if not record["identifier_source_xml"] and record["primary_source_xml"] and any(record[field] for field in IDENTIFIER_SOURCE_FIELDS):
        record["identifier_source_xml"] = record["primary_source_xml"]

    if parse_errors:
        record["parse_status"] = "partial_success" if record["parsed_xml_count"] else "failed"
        record["parse_notes"] = " || ".join(parse_errors)
    else:
        record["parse_status"] = "success" if record["parsed_xml_count"] else "failed"

    if not record["ppub_isbn"]:
        record["ppub_isbn"] = package_dir.name

    return record


def build_metadata_dataframe(input_root: Path, limit: int | None = None) -> pd.DataFrame:
    package_dirs = discover_packages(input_root)
    if limit is not None:
        package_dirs = package_dirs[:limit]

    records = [_merge_package_metadata(p) for p in package_dirs]
    df = pd.DataFrame(records)
    if df.empty:
        return df

    preferred_columns = [
        "package_folder", "package_path", "xml_file_count", "parsed_xml_count",
        "failed_xml_count", "primary_source_xml", "primary_source_role",
        "title_source_xml", "publication_date_source_xml", "identifier_source_xml",
        "fallback_used", "parse_status", "title_full", "title", "subtitle",
        "publication_title", "front_article_title", "issue_title", "book_title",
        "publication_date", "publication_time", "publication_day",
        "publication_month", "publication_year", "document_type",
        "document_type_code", "language", "authors", "editors", "prepared_by",
        "journal_title", "series_name", "series_number", "publisher_name",
        "publisher_location", "volume", "issue_number", "doi", "publisher_id",
        "translation_id", "stockcode", "repec", "docnumber", "ebook_isbn",
        "ppub_isbn", "epub_isbn", "pdf_isbn", "countries", "country_codes",
        "regions", "topics", "topic_codes", "keywords", "abstract",
        "elibrary_link", "elibrary_part_link", "copyright_statement",
        "copyright_year", "xml_files", "xml_roles", "failed_xml_files",
        "parse_notes",
    ]
    remaining_columns = [c for c in df.columns if c not in preferred_columns]
    df = df[preferred_columns + remaining_columns]
    return df.sort_values(by=["package_folder"]).reset_index(drop=True)


def write_metadata_workbook(df: pd.DataFrame, output_path: Path, input_root: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = [
        {"metric": "created_at", "value": datetime.now().isoformat(timespec="seconds")},
        {"metric": "input_root", "value": str(input_root)},
        {"metric": "package_count", "value": len(df)},
        {"metric": "success_count", "value": int((df["parse_status"] == "success").sum()) if not df.empty else 0},
        {"metric": "partial_success_count", "value": int((df["parse_status"] == "partial_success").sum()) if not df.empty else 0},
        {"metric": "failed_count", "value": int((df["parse_status"] == "failed").sum()) if not df.empty else 0},
        {"metric": "packages_with_fallback", "value": int(df["fallback_used"].fillna(False).astype(bool).sum()) if not df.empty else 0},
    ]
    summary_df = pd.DataFrame(summary_rows)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="metadata")
        summary_df.to_excel(writer, index=False, sheet_name="summary")

        metadata_sheet = writer.book["metadata"]
        summary_sheet = writer.book["summary"]
        metadata_sheet.freeze_panes = "A2"
        summary_sheet.freeze_panes = "A2"
        _autofit_worksheet_columns(metadata_sheet)
        _autofit_worksheet_columns(summary_sheet)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    input_root = args.input_root.resolve()
    output_path = resolve_output_path(input_root, args.output_path).resolve()

    df = build_metadata_dataframe(input_root=input_root, limit=args.limit)
    write_metadata_workbook(df, output_path=output_path, input_root=input_root)
    print(f"Wrote {len(df)} package rows to {output_path}")


if __name__ == "__main__":
    main()
