from __future__ import annotations

import argparse
import html.entities
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

_THIS_DIR = Path(__file__).resolve().parent
_TRACTION_DIR = _THIS_DIR.parent
if str(_TRACTION_DIR) not in sys.path:
    sys.path.insert(0, str(_TRACTION_DIR))

import config  # noqa: E402

XML_LANG_ATTR = "{http://www.w3.org/XML/1998/namespace}lang"
DEFAULT_INPUT_ROOT = Path(
    r"C:\Users\chuang\OneDrive - International Monetary Fund (PRD)\AI tools\Data\ArticleIV_Xml\spr_isr_com_articleiv_2024"
)

LIST_FIELDS = {
    "authors",
    "editors",
    "keywords",
    "country_codes",
    "countries",
    "regions",
    "topic_codes",
    "topics",
    "xml_files",
    "xml_roles",
    "failed_xml_files",
}

SINGLE_FIELDS = [
    "source_root_tag",
    "language",
    "document_type",
    "document_type_code",
    "title_full",
    "title",
    "subtitle",
    "front_article_title",
    "issue_title",
    "book_title",
    "publication_title",
    "journal_title",
    "series_name",
    "series_number",
    "publisher_name",
    "publisher_location",
    "publication_date",
    "publication_time",
    "publication_day",
    "publication_month",
    "publication_year",
    "volume",
    "issue_number",
    "doi",
    "publisher_id",
    "translation_id",
    "stockcode",
    "repec",
    "docnumber",
    "ebook_isbn",
    "ppub_isbn",
    "epub_isbn",
    "pdf_isbn",
    "abstract",
    "elibrary_link",
    "elibrary_part_link",
    "prepared_by",
    "copyright_statement",
    "copyright_year",
]

TITLE_SOURCE_FIELDS = {"title_full", "title", "subtitle", "publication_title", "issue_title", "book_title", "front_article_title"}
DATE_SOURCE_FIELDS = {"publication_date", "publication_time", "publication_day", "publication_month", "publication_year"}
IDENTIFIER_SOURCE_FIELDS = {
    "doi",
    "publisher_id",
    "translation_id",
    "stockcode",
    "repec",
    "docnumber",
    "ebook_isbn",
    "ppub_isbn",
    "epub_isbn",
    "pdf_isbn",
}

MONTH_LOOKUP = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}

XML_PREDEFINED_ENTITIES = {"amp", "lt", "gt", "apos", "quot"}
NAMED_ENTITY_PATTERN = re.compile(r"&([A-Za-z][A-Za-z0-9]+);")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract publication-level metadata from XML package folders into a consolidated Excel workbook."
    )
    parser.add_argument(
        "--input-root",
        type=Path,
        default=DEFAULT_INPUT_ROOT,
        help="Root directory whose direct subfolders are publication packages.",
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


def _local_name(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _clean_text(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _element_text(elem: ET.Element | None) -> str:
    if elem is None:
        return ""
    return _clean_text("".join(elem.itertext()))


def _iter_descendants(elem: ET.Element | None, tag_name: str | None = None) -> Iterable[ET.Element]:
    if elem is None:
        return []
    if tag_name is None:
        return elem.iter()
    return (node for node in elem.iter() if _local_name(node.tag) == tag_name)


def _direct_children(elem: ET.Element | None, tag_name: str | None = None) -> list[ET.Element]:
    if elem is None:
        return []
    children = list(elem)
    if tag_name is None:
        return children
    return [child for child in children if _local_name(child.tag) == tag_name]


def _find_first(elem: ET.Element | None, tag_name: str, attrs: dict[str, str] | None = None) -> ET.Element | None:
    if elem is None:
        return None
    attrs = attrs or {}
    for node in elem.iter():
        if _local_name(node.tag) != tag_name:
            continue
        if all(node.get(key) == value for key, value in attrs.items()):
            return node
    return None


def _find_all(elem: ET.Element | None, tag_name: str, attrs: dict[str, str] | None = None) -> list[ET.Element]:
    if elem is None:
        return []
    attrs = attrs or {}
    matches: list[ET.Element] = []
    for node in elem.iter():
        if _local_name(node.tag) != tag_name:
            continue
        if all(node.get(key) == value for key, value in attrs.items()):
            matches.append(node)
    return matches


def _join_unique(values: Iterable[str], sep: str = " | ") -> str:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        cleaned = _clean_text(value)
        if not cleaned:
            continue
        if cleaned not in seen:
            seen.add(cleaned)
            ordered.append(cleaned)
    return sep.join(ordered)


def _custom_meta_map(meta_parent: ET.Element | None) -> dict[str, list[str]]:
    output: dict[str, list[str]] = defaultdict(list)
    for custom_meta in _find_all(meta_parent, "custom-meta"):
        meta_name = _element_text(_find_first(custom_meta, "meta-name")).lower()
        meta_value = _element_text(_find_first(custom_meta, "meta-value"))
        if meta_name and meta_value:
            output[meta_name].append(meta_value)
    return dict(output)


def _pick_custom_meta(custom_meta: dict[str, list[str]], key: str) -> str:
    return _join_unique(custom_meta.get(key.lower(), []))


def _extract_titlepage_metadata(root: ET.Element) -> dict[str, str]:
    titlepage_title = ""
    prepared_by = ""
    for sec in _find_all(root, "sec"):
        sec_type = (sec.get("sec-type") or "").lower()
        sec_title = _element_text(_find_first(sec, "title")).lower()
        if sec_type != "titlepage" and sec_title != "title page":
            continue

        lines = [_element_text(child) for child in _direct_children(sec, "p")]
        lines = [line for line in lines if line]

        title_lines: list[str] = []
        for line in lines:
            lower_line = line.lower()
            if lower_line.startswith("approved by") or lower_line.startswith("prepared by"):
                break
            if _looks_like_date(line):
                break
            if line == line.upper() or lower_line.startswith("the "):
                title_lines.append(line.title())

        if not titlepage_title and title_lines:
            if len(title_lines) >= 2:
                titlepage_title = f"{title_lines[0]}: {title_lines[1]}"
            else:
                titlepage_title = title_lines[0]

        boxed_texts = [_element_text(node) for node in _find_all(sec, "boxed-text")]
        prepared_lines = [line for line in lines if line.lower().startswith("prepared by")]
        prepared_by = _join_unique(prepared_lines + boxed_texts)
        break

    return {
        "titlepage_title": titlepage_title,
        "prepared_by": prepared_by,
    }


def _looks_like_date(value: str) -> bool:
    cleaned = _clean_text(value).lower()
    if not cleaned:
        return False
    if re.fullmatch(r"\d{4}", cleaned):
        return True
    month_pattern = "|".join(MONTH_LOOKUP)
    if re.search(rf"\b({month_pattern})\b", cleaned):
        return True
    return bool(re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", cleaned))


def _split_title_and_subtitle(title_full: str, explicit_subtitle: str = "") -> tuple[str, str]:
    title_full = _clean_text(title_full)
    explicit_subtitle = _clean_text(explicit_subtitle)
    if explicit_subtitle:
        if title_full.endswith(f": {explicit_subtitle}"):
            title = title_full[: -(len(explicit_subtitle) + 2)]
            return _clean_text(title), explicit_subtitle
        return title_full, explicit_subtitle
    if ":" in title_full:
        title, subtitle = title_full.split(":", 1)
        return _clean_text(title), _clean_text(subtitle)
    return title_full, ""


def _replace_non_xml_named_entities(xml_text: str) -> str:
    def _replacement(match: re.Match[str]) -> str:
        entity_name = match.group(1)
        if entity_name in XML_PREDEFINED_ENTITIES:
            return match.group(0)

        html5_value = html.entities.html5.get(f"{entity_name};")
        if html5_value is not None:
            return html5_value

        entitydef_value = html.entities.entitydefs.get(entity_name)
        if entitydef_value is not None:
            return entitydef_value

        return match.group(0)

    return NAMED_ENTITY_PATTERN.sub(_replacement, xml_text)


def _safe_parse_xml(xml_path: Path) -> ET.ElementTree:
    try:
        return ET.parse(xml_path)
    except ET.ParseError as exc:
        if "undefined entity" not in str(exc).lower():
            raise
        xml_text = xml_path.read_text(encoding="utf-8")
        xml_text = _replace_non_xml_named_entities(xml_text)
        return ET.ElementTree(ET.fromstring(xml_text))


def _choose_pub_date(meta_parent: ET.Element | None) -> ET.Element | None:
    pub_dates = _find_all(meta_parent, "pub-date")
    if not pub_dates:
        return None
    preferred_attrs = [
        {"pub-type": "ppub"},
        {"date-type": "ppub"},
        {"publication-format": "print", "date-type": "ppub"},
    ]
    for attr_set in preferred_attrs:
        for pub_date in pub_dates:
            if all(pub_date.get(key) == value for key, value in attr_set.items()):
                return pub_date
    return pub_dates[0]


def _build_date_parts(pub_date: ET.Element | None) -> dict[str, str]:
    if pub_date is None:
        return {
            "publication_date": "",
            "publication_time": "",
            "publication_day": "",
            "publication_month": "",
            "publication_year": "",
        }

    year = _element_text(_find_first(pub_date, "year"))
    month = _element_text(_find_first(pub_date, "month"))
    day = _element_text(_find_first(pub_date, "day"))

    if month and not month.isdigit():
        month = MONTH_LOOKUP.get(month.lower(), month)
    if month.isdigit():
        month = month.zfill(2)
    if day.isdigit():
        day = day.zfill(2)

    publication_date = ""
    if year and month and day:
        publication_date = f"{year}-{month}-{day}"
    elif year and month:
        publication_date = f"{year}-{month}"
    elif year:
        publication_date = year

    return {
        "publication_date": publication_date,
        "publication_time": "",
        "publication_day": day,
        "publication_month": month,
        "publication_year": year,
    }


def _extract_identifiers(meta_parent: ET.Element | None) -> dict[str, str]:
    identifiers = {
        "doi": "",
        "publisher_id": "",
        "translation_id": "",
        "stockcode": "",
        "repec": "",
        "docnumber": "",
    }

    for tag_name, attr_name in (("issue-id", "pub-id-type"), ("article-id", "pub-id-type"), ("book-id", "book-id-type"), ("journal-id", "journal-id-type")):
        for node in _find_all(meta_parent, tag_name):
            id_type = (node.get(attr_name) or "").lower()
            if not id_type:
                continue
            value = _element_text(node)
            if not value:
                continue
            if id_type == "doi" and not identifiers["doi"]:
                identifiers["doi"] = value
            elif id_type == "publisher-id" and not identifiers["publisher_id"]:
                identifiers["publisher_id"] = value
            elif id_type == "translation" and not identifiers["translation_id"]:
                identifiers["translation_id"] = value
            elif id_type == "stockcode" and not identifiers["stockcode"]:
                identifiers["stockcode"] = value
            elif id_type == "repec" and not identifiers["repec"]:
                identifiers["repec"] = value
            elif id_type == "docnumber" and not identifiers["docnumber"]:
                identifiers["docnumber"] = value
    return identifiers


def _extract_isbns(meta_parent: ET.Element | None) -> dict[str, str]:
    isbns = {
        "ebook_isbn": "",
        "ppub_isbn": "",
        "epub_isbn": "",
        "pdf_isbn": "",
    }
    publication_key_map = {
        "ebook": "ebook_isbn",
        "ppub": "ppub_isbn",
        "epub": "epub_isbn",
        "pdf": "pdf_isbn",
        "print": "ppub_isbn",
    }
    for node in _find_all(meta_parent, "isbn"):
        publication_format = (node.get("publication-format") or "").lower()
        target_key = publication_key_map.get(publication_format)
        if not target_key or isbns[target_key]:
            continue
        isbns[target_key] = _element_text(node)
    return isbns


def _extract_contributors(meta_parent: ET.Element | None) -> dict[str, str]:
    authors: list[str] = []
    editors: list[str] = []
    for contrib in _find_all(meta_parent, "contrib"):
        contrib_type = (contrib.get("contrib-type") or "").lower()
        name_parts = [
            _element_text(_find_first(contrib, "surname")),
            _element_text(_find_first(contrib, "given-names")),
        ]
        full_name = _join_unique(name_parts, sep=", ")
        if not full_name:
            full_name = _element_text(_find_first(contrib, "string-name"))
        if not full_name:
            full_name = _element_text(_find_first(contrib, "name"))
        if not full_name:
            full_name = _element_text(contrib)
        if not full_name:
            continue
        if contrib_type == "editor":
            editors.append(full_name)
        else:
            authors.append(full_name)
    return {
        "authors": _join_unique(authors),
        "editors": _join_unique(editors),
    }


def _extract_subjects(meta_parent: ET.Element | None) -> dict[str, str]:
    country_codes: list[str] = []
    countries: list[str] = []
    regions: list[str] = []
    topic_codes: list[str] = []
    topics: list[str] = []

    for subj_group in _find_all(meta_parent, "subj-group"):
        group_type = (subj_group.get("subj-group-type") or "").lower()
        for compound_subject in _find_all(subj_group, "compound-subject"):
            code = ""
            text = ""
            international_region = ""
            for part in _find_all(compound_subject, "compound-subject-part"):
                content_type = (part.get("content-type") or "").lower()
                value = _element_text(part)
                if not value:
                    continue
                if content_type == "code" and not code:
                    code = value
                elif content_type == "text" and not text:
                    text = value
                elif content_type == "international-region" and not international_region:
                    international_region = value

            if group_type == "iso-3166-1":
                if code:
                    country_codes.append(code)
                if text:
                    countries.append(text)
                if international_region:
                    regions.append(international_region)
            elif group_type == "imf-region":
                if code:
                    regions.append(code)
                if text:
                    regions.append(text)
            elif group_type == "ebv-ef-topics":
                if code:
                    topic_codes.append(code)
                if text:
                    topics.append(text)

    return {
        "country_codes": _join_unique(country_codes),
        "countries": _join_unique(countries),
        "regions": _join_unique(regions),
        "topic_codes": _join_unique(topic_codes),
        "topics": _join_unique(topics),
    }


def _extract_keywords(meta_parent: ET.Element | None, custom_meta: dict[str, list[str]]) -> str:
    keywords = [_element_text(node) for node in _find_all(meta_parent, "kwd")]
    keywords.extend(custom_meta.get("keywords", []))
    return _join_unique(keywords)


def _extract_title_fields(root: ET.Element, meta_parent: ET.Element | None, custom_meta: dict[str, list[str]]) -> dict[str, str]:
    titlepage_metadata = _extract_titlepage_metadata(root)

    publication_title = _pick_custom_meta(custom_meta, "publication title")
    issue_title = _element_text(_find_first(meta_parent, "issue-title"))
    article_title = _element_text(_find_first(meta_parent, "article-title"))
    book_title = _element_text(_find_first(meta_parent, "book-title"))
    book_subtitle = _element_text(_find_first(meta_parent, "book-subtitle"))

    title_candidates = [
        publication_title,
        issue_title,
        book_title,
        "" if article_title.lower() == "front matter" else article_title,
        titlepage_metadata["titlepage_title"],
    ]
    title_full = next((candidate for candidate in title_candidates if candidate), "")
    title, subtitle = _split_title_and_subtitle(title_full, explicit_subtitle=book_subtitle)

    return {
        "title_full": title_full,
        "title": title,
        "subtitle": subtitle,
        "front_article_title": article_title,
        "issue_title": issue_title,
        "book_title": book_title,
        "publication_title": publication_title,
        "prepared_by": titlepage_metadata["prepared_by"],
    }


def _extract_document_type(root: ET.Element, meta_parent: ET.Element | None, custom_meta: dict[str, list[str]]) -> dict[str, str]:
    root_tag = _local_name(root.tag)
    if root_tag == "issue-xml":
        issue_meta = _find_first(root, "issue-meta")
        return {
            "document_type": "issue",
            "document_type_code": (issue_meta.get("issue-type") if issue_meta is not None else "") or _pick_custom_meta(custom_meta, "issue-type"),
        }
    if root_tag == "article":
        return {
            "document_type": "article",
            "document_type_code": root.get("article-type", ""),
        }
    if root_tag == "book":
        return {
            "document_type": "book",
            "document_type_code": root.get("book-type", ""),
        }
    return {
        "document_type": root_tag,
        "document_type_code": "",
    }


def _extract_abstract(meta_parent: ET.Element | None, custom_meta: dict[str, list[str]]) -> str:
    abstract_text = _element_text(_find_first(meta_parent, "abstract"))
    if abstract_text:
        return abstract_text
    return _pick_custom_meta(custom_meta, "abstract")


def parse_xml_file(xml_path: Path) -> dict[str, Any]:
    tree = _safe_parse_xml(xml_path)
    root = tree.getroot()
    root_tag = _local_name(root.tag)

    if root_tag == "issue-xml":
        meta_parent = _find_first(root, "issue-meta")
        journal_meta = _find_first(root, "journal-meta")
    elif root_tag == "article":
        meta_parent = _find_first(root, "article-meta")
        journal_meta = _find_first(root, "journal-meta")
    elif root_tag == "book":
        meta_parent = _find_first(root, "book-meta")
        journal_meta = meta_parent
    else:
        meta_parent = root
        journal_meta = root

    custom_meta = _custom_meta_map(meta_parent)
    date_parts = _build_date_parts(_choose_pub_date(meta_parent))
    title_fields = _extract_title_fields(root, meta_parent, custom_meta)
    identifier_fields = _extract_identifiers(meta_parent)
    isbn_fields = _extract_isbns(meta_parent)
    contributor_fields = _extract_contributors(meta_parent)
    subject_fields = _extract_subjects(meta_parent)
    document_type_fields = _extract_document_type(root, meta_parent, custom_meta)

    return {
        "source_root_tag": root_tag,
        "language": root.get(XML_LANG_ATTR, "") or root.get("lang", ""),
        **document_type_fields,
        **title_fields,
        "journal_title": _element_text(_find_first(journal_meta, "journal-title")),
        "series_name": _pick_custom_meta(custom_meta, "series name"),
        "series_number": _pick_custom_meta(custom_meta, "series number"),
        "publisher_name": _element_text(_find_first(journal_meta, "publisher-name")) or _pick_custom_meta(custom_meta, "publisher"),
        "publisher_location": _element_text(_find_first(journal_meta, "publisher-loc")),
        **date_parts,
        "volume": _element_text(_find_first(meta_parent, "volume")),
        "issue_number": _element_text(_find_first(meta_parent, "issue")),
        **identifier_fields,
        **isbn_fields,
        **contributor_fields,
        "abstract": _extract_abstract(meta_parent, custom_meta),
        "keywords": _extract_keywords(meta_parent, custom_meta),
        **subject_fields,
        "elibrary_link": _pick_custom_meta(custom_meta, "elibrary link"),
        "elibrary_part_link": _pick_custom_meta(custom_meta, "elibrary-part link"),
        "copyright_statement": _element_text(_find_first(meta_parent, "copyright-statement")),
        "copyright_year": _element_text(_find_first(meta_parent, "copyright-year")),
    }


def _xml_role(xml_path: Path) -> str:
    name = xml_path.name.lower()
    if "resource-manifest" in name:
        if re.search(r"-ch\d{3}-", name):
            return "chapter_manifest"
        return "resource_manifest"
    if "issue" in name:
        return "issue"
    match = re.search(r"-a(\d{3})-", name)
    if match:
        article_number = int(match.group(1))
        if article_number == 0:
            return "front_matter"
        return f"article_{article_number:03d}"
    if name.endswith("-book.xml") or re.search(r"-en-book\.xml$", name):
        return "book"
    return "other"


def _xml_priority(xml_path: Path) -> tuple[int, int, str]:
    role = _xml_role(xml_path)
    if role == "issue":
        return (0, 0, xml_path.name.lower())
    if role == "book":
        return (0, 1, xml_path.name.lower())
    if role.startswith("article_"):
        return (1, int(role.split("_")[1]), xml_path.name.lower())
    if role == "front_matter":
        return (2, 0, xml_path.name.lower())
    if role == "resource_manifest":
        return (4, 0, xml_path.name.lower())
    if role == "chapter_manifest":
        return (4, 1, xml_path.name.lower())
    return (3, 0, xml_path.name.lower())


def discover_packages(input_root: Path) -> list[Path]:
    if not input_root.exists():
        raise FileNotFoundError(f"Input root does not exist: {input_root}")
    packages = [path for path in input_root.iterdir() if path.is_dir()]
    return sorted(packages, key=lambda path: path.name)


def discover_xml_files(package_dir: Path) -> list[Path]:
    xml_files = [path for path in package_dir.iterdir() if path.is_file() and path.suffix.lower() == ".xml"]
    return sorted(xml_files, key=_xml_priority)


def _empty_package_record(package_dir: Path, xml_files: list[Path]) -> dict[str, Any]:
    record: dict[str, Any] = {
        "package_folder": package_dir.name,
        "package_path": str(package_dir),
        "xml_file_count": len(xml_files),
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
        "xml_files": _join_unique(path.name for path in xml_files),
        "xml_roles": _join_unique(_xml_role(path) for path in xml_files),
        "failed_xml_files": "",
    }
    for field in SINGLE_FIELDS:
        record[field] = ""
    for field in LIST_FIELDS - {"xml_files", "xml_roles", "failed_xml_files"}:
        record[field] = ""
    return record


def _merge_package_metadata(package_dir: Path) -> dict[str, Any]:
    xml_files = discover_xml_files(package_dir)
    record = _empty_package_record(package_dir, xml_files)
    aggregate_lists: dict[str, list[str]] = {field: [] for field in LIST_FIELDS}
    parse_errors: list[str] = []

    for index, xml_path in enumerate(xml_files):
        try:
            xml_metadata = parse_xml_file(xml_path)
        except Exception as exc:  # noqa: BLE001
            record["failed_xml_count"] += 1
            aggregate_lists["failed_xml_files"].append(xml_path.name)
            parse_errors.append(f"{xml_path.name}: {type(exc).__name__}: {exc}")
            continue

        record["parsed_xml_count"] += 1
        if not record["primary_source_xml"]:
            record["primary_source_xml"] = xml_path.name
            record["primary_source_role"] = _xml_role(xml_path)
            record["source_root_tag"] = xml_metadata.get("source_root_tag", "")

        for field in LIST_FIELDS - {"xml_files", "xml_roles", "failed_xml_files"}:
            value = xml_metadata.get(field, "")
            if value:
                aggregate_lists[field].extend(part for part in value.split(" | ") if part)

        for field in SINGLE_FIELDS:
            value = _clean_text(str(xml_metadata.get(field, "")))
            if not value:
                continue
            if not record[field]:
                record[field] = value
                if index > 0:
                    record["fallback_used"] = True
                if field in TITLE_SOURCE_FIELDS and not record["title_source_xml"]:
                    record["title_source_xml"] = xml_path.name
                if field in DATE_SOURCE_FIELDS and not record["publication_date_source_xml"]:
                    record["publication_date_source_xml"] = xml_path.name
                if field in IDENTIFIER_SOURCE_FIELDS and not record["identifier_source_xml"]:
                    record["identifier_source_xml"] = xml_path.name

    for field, values in aggregate_lists.items():
        joined = _join_unique(values)
        if joined:
            record[field] = joined

    if not record["title"] and record["title_full"]:
        record["title"], record["subtitle"] = _split_title_and_subtitle(record["title_full"], explicit_subtitle=record["subtitle"])

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

    records = [_merge_package_metadata(package_dir) for package_dir in package_dirs]
    df = pd.DataFrame(records)
    if df.empty:
        return df

    preferred_columns = [
        "package_folder",
        "package_path",
        "xml_file_count",
        "parsed_xml_count",
        "failed_xml_count",
        "primary_source_xml",
        "primary_source_role",
        "title_source_xml",
        "publication_date_source_xml",
        "identifier_source_xml",
        "fallback_used",
        "parse_status",
        "title_full",
        "title",
        "subtitle",
        "publication_title",
        "front_article_title",
        "issue_title",
        "book_title",
        "publication_date",
        "publication_time",
        "publication_day",
        "publication_month",
        "publication_year",
        "document_type",
        "document_type_code",
        "language",
        "authors",
        "editors",
        "prepared_by",
        "journal_title",
        "series_name",
        "series_number",
        "publisher_name",
        "publisher_location",
        "volume",
        "issue_number",
        "doi",
        "publisher_id",
        "translation_id",
        "stockcode",
        "repec",
        "docnumber",
        "ebook_isbn",
        "ppub_isbn",
        "epub_isbn",
        "pdf_isbn",
        "countries",
        "country_codes",
        "regions",
        "topics",
        "topic_codes",
        "keywords",
        "abstract",
        "elibrary_link",
        "elibrary_part_link",
        "copyright_statement",
        "copyright_year",
        "xml_files",
        "xml_roles",
        "failed_xml_files",
        "parse_notes",
    ]
    remaining_columns = [column for column in df.columns if column not in preferred_columns]
    df = df[preferred_columns + remaining_columns]
    return df.sort_values(by=["package_folder"]).reset_index(drop=True)


def _autofit_worksheet_columns(worksheet: Any) -> None:
    for column_cells in worksheet.columns:
        values = [str(cell.value) for cell in column_cells if cell.value is not None]
        if not values:
            continue
        max_length = min(max(len(value) for value in values) + 2, 80)
        worksheet.column_dimensions[column_cells[0].column_letter].width = max_length


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


def resolve_output_path(input_root: Path, output_path: Path | None) -> Path:
    if output_path is not None:
        return output_path
    return config.output_dir / "incremental_update" / f"{input_root.name}_metadata.xlsx"


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    input_root = args.input_root.resolve()
    output_path = resolve_output_path(input_root, args.output_path).resolve()

    df = build_metadata_dataframe(input_root=input_root, limit=args.limit)
    write_metadata_workbook(df, output_path=output_path, input_root=input_root)
    print(f"Wrote {len(df)} package rows to {output_path}")


if __name__ == "__main__":
    main()
