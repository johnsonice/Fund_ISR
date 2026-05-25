from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_THIS_DIR = Path(__file__).resolve().parent
_TRACTION_DIR = _THIS_DIR.parent
if str(_TRACTION_DIR) not in sys.path:
    sys.path.insert(0, str(_TRACTION_DIR))

import config  # noqa: E402
from data_preprocess import doc_to_paragraphs, extract_StaffAppraisal_and_Buff  # noqa: E402

DEFAULT_RAW_XML_ROOT = Path(
    r"C:\Users\chuang\OneDrive - International Monetary Fund (PRD)\AI tools\Data\ArticleIV_xml_updated\05252026_update"
)
DEFAULT_METADATA_PATH = Path(
    r"C:\Users\chuang\OneDrive - International Monetary Fund (PRD)\Faltermeier, Julia's files - FIP Traction of IMF surveillance\data\aiv\IMF_Main_MetaData_20260525_filtered.xlsx"
)
DEFAULT_OUTPUT_DIR = config.output_dir / "incremental_update" / DEFAULT_RAW_XML_ROOT.name


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an incremental AIV extraction on nested XML update folders using a filtered metadata workbook."
    )
    parser.add_argument(
        "--raw-xml-root",
        type=Path,
        default=DEFAULT_RAW_XML_ROOT,
        help=f"Nested XML update root. Default: {DEFAULT_RAW_XML_ROOT}",
    )
    parser.add_argument(
        "--metadata-path",
        type=Path,
        default=DEFAULT_METADATA_PATH,
        help=f"Filtered metadata workbook path. Default: {DEFAULT_METADATA_PATH}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for incremental artifacts. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--existing-doc-csv",
        type=Path,
        default=None,
        help="Optional existing document-level CSV whose Print ISBNs should be skipped.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional package limit for testing.",
    )
    parser.add_argument(
        "--process-all-discovered",
        action="store_true",
        help="If set, process all discovered package folders instead of restricting to the metadata workbook ISBNs.",
    )
    return parser.parse_args(argv)


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return " ".join(str(value).split()).strip()


def _split_pipe_first(value: Any) -> str:
    cleaned = _clean_text(value)
    if not cleaned:
        return ""
    return cleaned.split(" | ")[0].strip()


def _split_title_and_subtitle(title_full: Any) -> tuple[str, str]:
    cleaned = _clean_text(title_full)
    if not cleaned:
        return "", ""
    if ":" not in cleaned:
        return cleaned, ""
    title, subtitle = cleaned.split(":", 1)
    return title.strip(), subtitle.strip()


def discover_package_folders(raw_xml_root: Path) -> tuple[dict[str, str], dict[str, list[str]]]:
    folder_dict: dict[str, str] = {}
    duplicates: dict[str, list[str]] = {}

    for candidate in sorted((path for path in raw_xml_root.rglob("*") if path.is_dir()), key=lambda p: str(p)):
        try:
            child_xmls = [child for child in candidate.iterdir() if child.is_file() and child.suffix.lower() == ".xml"]
        except PermissionError:
            continue

        if not child_xmls:
            continue

        package_id = candidate.name
        candidate_str = str(candidate)
        if package_id in folder_dict:
            duplicates.setdefault(package_id, [folder_dict[package_id]]).append(candidate_str)
            continue
        folder_dict[package_id] = candidate_str

    return folder_dict, duplicates


def load_metadata(metadata_path: Path) -> pd.DataFrame:
    df_meta = pd.read_excel(metadata_path)
    if "Print ISBN" not in df_meta.columns:
        raise ValueError("Metadata workbook must contain a 'Print ISBN' column")

    df_meta = df_meta.copy()
    if "package_path" in df_meta.columns:
        df_meta = df_meta.rename(columns={"package_path": "metadata_package_path"})
    df_meta["Print ISBN"] = df_meta["Print ISBN"].astype(str).str.strip()
    df_meta = df_meta.drop_duplicates(subset=["Print ISBN"]).reset_index(drop=True)

    if "title_full" not in df_meta.columns:
        raise ValueError("Metadata workbook must contain a 'title_full' column")

    title_parts = df_meta["title_full"].apply(_split_title_and_subtitle)
    df_meta["Title"] = [title for title, _ in title_parts]
    df_meta["Subtitle"] = [subtitle for _, subtitle in title_parts]
    df_meta["Full Title"] = df_meta["title_full"].fillna("")
    df_meta["Extract text after :"] = df_meta["Subtitle"]
    df_meta['Extract text after ":"'] = df_meta["Subtitle"]
    df_meta["Primary Country Code"] = df_meta.get("country_codes", pd.Series([""] * len(df_meta))).apply(_split_pipe_first)
    df_meta["Primary Country Description"] = df_meta.get("countries", pd.Series([""] * len(df_meta))).apply(_split_pipe_first)
    df_meta["Publication Date"] = df_meta.get("publication_date", pd.Series([""] * len(df_meta))).fillna("")
    return df_meta


def _package_paths_df(folder_dict: dict[str, str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Print ISBN": list(folder_dict.keys()),
            "package_path": list(folder_dict.values()),
        }
    )


def _list_has_content(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0


def _serialize_for_csv(value: Any) -> Any:
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, str):
        return value.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")
    return value


def _prepare_dataframe_for_csv(df: pd.DataFrame) -> pd.DataFrame:
    df_csv = df.copy()
    for column in df_csv.columns:
        if pd.api.types.is_object_dtype(df_csv[column]):
            df_csv[column] = df_csv[column].map(_serialize_for_csv)
    return df_csv


def _write_csv(df: pd.DataFrame, output_path: Path) -> None:
    df_csv = _prepare_dataframe_for_csv(df)
    df_csv.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
        quoting=csv.QUOTE_ALL,
        lineterminator="\n",
    )


def build_incremental_doc_df(
    df_meta: pd.DataFrame,
    folder_dict: dict[str, str],
    staff_dict: dict[str, str],
    staff_content_dict: dict[str, str],
    text_sa_dict: dict[str, str],
    para_sa_dict: dict[str, list[str]],
    buff_dict: dict[str, str],
    buff_content_dict: dict[str, str],
    para_bu_dict: dict[str, list[str]],
    para_sr_dict: dict[str, list[str]],
    para_av_dict: dict[str, list[str]],
    av_uncertain_dict: dict[str, bool],
) -> pd.DataFrame:
    extraction_df = pd.DataFrame(
        {
            "Print ISBN": list(folder_dict.keys()),
            "filename_staff": [staff_dict.get(key) for key in folder_dict],
            "text_staff": [staff_content_dict.get(key) for key in folder_dict],
            "filename_buff": [buff_dict.get(key) for key in folder_dict],
            "text_buff": [buff_content_dict.get(key) for key in folder_dict],
            "text_sa": [text_sa_dict.get(key) for key in folder_dict],
            "paragraphs_sa": [para_sa_dict.get(key) for key in folder_dict],
            "paragraphs_bu": [para_bu_dict.get(key) for key in folder_dict],
            "paragraphs_sr": [para_sr_dict.get(key) for key in folder_dict],
            "paragraphs_av": [para_av_dict.get(key) for key in folder_dict],
            "av_uncertain": [av_uncertain_dict.get(key, True) for key in folder_dict],
        }
    )

    extraction_df["Print ISBN"] = extraction_df["Print ISBN"].astype(str)
    extraction_df = extraction_df.merge(_package_paths_df(folder_dict), on="Print ISBN", how="left")
    extraction_df = extraction_df.merge(df_meta, on="Print ISBN", how="left", indicator="metadata_merge_status")
    extraction_df["metadata_matched"] = extraction_df["metadata_merge_status"].eq("both")
    extraction_df = extraction_df.drop(columns=["metadata_merge_status"])

    extraction_df["buff_verified"] = extraction_df["paragraphs_bu"].apply(_list_has_content)
    extraction_df["staff_verified"] = extraction_df["paragraphs_sa"].apply(_list_has_content)
    extraction_df["has_buff"] = extraction_df.get("title_full", pd.Series([""] * len(extraction_df))).fillna("").astype(str).str.lower().str.contains("statement by|statement on", regex=True)

    def _should_drop_buff(row: pd.Series) -> bool:
        if row["has_buff"] or not row["buff_verified"] or not isinstance(row["paragraphs_bu"], list):
            return False
        joined = " ".join(row["paragraphs_bu"]).lower()
        return "does not alter" in joined or "does not change" in joined

    drop_buff_mask = extraction_df.apply(_should_drop_buff, axis=1)
    extraction_df.loc[drop_buff_mask, "paragraphs_bu"] = pd.NA
    extraction_df["buff_verified"] = extraction_df["paragraphs_bu"].apply(_list_has_content)

    if "Full Title" in extraction_df.columns:
        extraction_df["Full Title"] = extraction_df["Full Title"].fillna(extraction_df.get("title_full", ""))
    else:
        extraction_df["Full Title"] = extraction_df.get("title_full", "")

    if "Title" in extraction_df.columns:
        extraction_df["Title"] = extraction_df["Title"].fillna(extraction_df.get("Country Name from title", ""))
    else:
        extraction_df["Title"] = extraction_df.get("Country Name from title", "")

    if "Subtitle" not in extraction_df.columns:
        extraction_df["Subtitle"] = extraction_df.get('Extract text after ":"', "")

    if "Publication Date" not in extraction_df.columns:
        extraction_df["Publication Date"] = extraction_df.get("publication_date", "")

    return extraction_df


def write_summary(
    output_path: Path,
    raw_xml_root: Path,
    metadata_path: Path,
    folder_dict: dict[str, str],
    duplicates: dict[str, list[str]],
    selected_isbns: list[str],
    missing_from_discovery: list[str],
    unmatched_in_metadata: list[str],
    df_doc: pd.DataFrame,
    df_paragraphs: pd.DataFrame,
) -> None:
    summary = {
        "raw_xml_root": str(raw_xml_root),
        "metadata_path": str(metadata_path),
        "discovered_package_count": len(folder_dict),
        "selected_package_count": len(selected_isbns),
        "duplicate_package_ids": duplicates,
        "missing_from_discovery": missing_from_discovery,
        "unmatched_in_metadata": unmatched_in_metadata,
        "document_rows": int(len(df_doc)),
        "paragraph_rows": int(len(df_paragraphs)),
        "staff_verified_count": int(df_doc["staff_verified"].sum()) if "staff_verified" in df_doc.columns else 0,
        "buff_verified_count": int(df_doc["buff_verified"].sum()) if "buff_verified" in df_doc.columns else 0,
        "metadata_matched_count": int(df_doc["metadata_matched"].sum()) if "metadata_matched" in df_doc.columns else 0,
    }
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    raw_xml_root = args.raw_xml_root.resolve()
    metadata_path = args.metadata_path.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    folder_dict_all, duplicates = discover_package_folders(raw_xml_root)
    if not folder_dict_all:
        raise FileNotFoundError(f"No package folders with XML files found under {raw_xml_root}")

    df_meta = load_metadata(metadata_path)
    metadata_isbns = df_meta["Print ISBN"].astype(str).tolist()

    if args.process_all_discovered:
        selected_isbns = sorted(folder_dict_all)
    else:
        selected_isbns = [isbn for isbn in metadata_isbns if isbn in folder_dict_all]

    missing_from_discovery = sorted([isbn for isbn in metadata_isbns if isbn not in folder_dict_all])

    if args.existing_doc_csv is not None:
        existing_df = pd.read_csv(args.existing_doc_csv)
        if "Print ISBN" not in existing_df.columns:
            raise ValueError("Existing document CSV must contain a 'Print ISBN' column")
        existing_isbns = set(existing_df["Print ISBN"].astype(str))
        selected_isbns = [isbn for isbn in selected_isbns if isbn not in existing_isbns]

    if args.limit is not None:
        selected_isbns = selected_isbns[: args.limit]

    selected_folder_dict = {isbn: folder_dict_all[isbn] for isbn in selected_isbns}
    if not selected_folder_dict:
        raise ValueError("No package folders selected for incremental processing")

    (
        staff_dict,
        staff_content_dict,
        text_sa_dict,
        para_sa_dict,
        buff_dict,
        buff_content_dict,
        para_bu_dict,
        para_sr_dict,
        para_av_dict,
        av_uncertain_dict,
    ) = extract_StaffAppraisal_and_Buff(selected_folder_dict)

    df_doc = build_incremental_doc_df(
        df_meta=df_meta,
        folder_dict=selected_folder_dict,
        staff_dict=staff_dict,
        staff_content_dict=staff_content_dict,
        text_sa_dict=text_sa_dict,
        para_sa_dict=para_sa_dict,
        buff_dict=buff_dict,
        buff_content_dict=buff_content_dict,
        para_bu_dict=para_bu_dict,
        para_sr_dict=para_sr_dict,
        para_av_dict=para_av_dict,
        av_uncertain_dict=av_uncertain_dict,
    )

    doc_output_path = output_dir / "df_aiv_incremental.csv"
    _write_csv(df_doc, doc_output_path)

    df_doc_reload = pd.read_csv(doc_output_path)
    df_paragraphs = doc_to_paragraphs(df_doc_reload)
    paragraph_output_path = output_dir / "df_paragraphs_incremental.csv"
    _write_csv(df_paragraphs, paragraph_output_path)

    processed_set = set(df_doc["Print ISBN"].astype(str))
    unmatched_in_metadata = sorted([isbn for isbn in processed_set if isbn not in set(df_meta["Print ISBN"].astype(str))])

    write_summary(
        output_path=output_dir / "incremental_summary.json",
        raw_xml_root=raw_xml_root,
        metadata_path=metadata_path,
        folder_dict=folder_dict_all,
        duplicates=duplicates,
        selected_isbns=selected_isbns,
        missing_from_discovery=missing_from_discovery,
        unmatched_in_metadata=unmatched_in_metadata,
        df_doc=df_doc,
        df_paragraphs=df_paragraphs,
    )

    print(f"Discovered package folders: {len(folder_dict_all)}")
    print(f"Selected package folders: {len(selected_folder_dict)}")
    print(f"Wrote document-level incremental data to {doc_output_path}")
    print(f"Wrote paragraph-level incremental data to {paragraph_output_path}")
    print(f"Wrote summary to {output_dir / 'incremental_summary.json'}")


if __name__ == "__main__":
    main()
