"""
LLM-based classifier for IMF Article IV disagreement area labels.

Maps fine-grained disagreement area strings (e.g. "monetary policy tightening",
"exchange rate flexibility") to predefined higher-level categories per sector
(e.g. "Monetary Policy Direction", "Foreign Exchange Policies").

Uses a JSON cache so the LLM is only called for new/unseen labels. On repeated
runs (e.g. re-running the analysis notebook), all labels hit the cache and no
LLM calls are made.

Usage as a library:
    from classify_disagreement_areas import classify_areas_batch
    mapping = classify_areas_batch(["monetary policy tightening", "FX intervention"],
                                   sector="Monetary")
    # => {"monetary policy tightening": "Monetary Policy Direction",
    #     "fx intervention": "Monetary Policy Operations"}

Usage as CLI:
    # Pre-seed cache from reference notebook's field_dict entries
    python classify_disagreement_areas.py --preseed

    # Classify all areas in a general-agreement CSV
    python classify_disagreement_areas.py \\
      --data-file /path/to/df_documents_general.csv

    # Classify specific areas
    python classify_disagreement_areas.py \\
      --sector Monetary \\
      --areas "monetary policy tightening" "exchange rate flexibility"
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Sequence

import pandas as pd

_THIS_DIR = Path(__file__).resolve().parent
_TRACTION_DIR = _THIS_DIR.parent
_REPO_ROOT = _TRACTION_DIR.parents[1]

DEFAULT_CACHE_PATH = _THIS_DIR / "disagreement_area_cache.json"

SECTOR_CATEGORIES: dict[str, list[str]] = {
    "Monetary": [
        "Monetary Policy Framework",
        "Monetary Policy Direction",
        "Monetary Policy Operations",
        "Foreign Exchange Policies",
        "Inflation",
        "Interest Rate",
        "Other",
    ],
    "Fiscal": [
        "Fiscal Consolidation and Adjustment",
        "Tax Policy and Administration",
        "Debt Management and Sustainability",
        "Public Spending and Investment",
        "Fiscal Framework and Transparency",
        "Other",
    ],
    "External": [
        "Exchange Rate Policies",
        "Current Account Assessments",
        "External Stability",
        "External Financing",
        "Trade Policies",
        "Reserves Management",
        "Competitiveness",
        "External Debt Management",
        "Financial Flows and Interventions",
        "Other",
    ],
    "Financial": [
        "Macroprudential Policy",
        "Banking Sector Dynamics",
        "Non-Performing Loans",
        "Regulation",
        "Financial Sector Reforms",
        "Housing Market",
        "Credit and Liquidity",
        "Interest Rate",
        "Financial Crisis",
        "Market Risks",
        "Other",
    ],
    "Real": [
        "Growth Outlook",
        "Inflation",
        "Structural Reform",
        "Labor Market",
        "Economic Outlook",
        "Sectoral Growth",
        "Market and Economic Conditions",
        "External Factors",
        "Other",
    ],
    # Cross-sector / "Other" bucket. The v1 general-agreement schema called
    # this `other_areas` (a single free-text list); v2 promotes it to a
    # first-class sector named `Other_Sector` alongside its own
    # Agreement_Other score. Same conceptual categories on both sides.
    "Other": [
        "Labor Market",
        "Climate Change and Environment",
        "Governance and Anti-Corruption",
        "Diversification",
        "Structural Reforms",
        "Energy Sector",
        "Immigration and Trade",
        "Housing Market",
        "Infrastructure Investment",
        "Fiscal Reforms",
        "SOE Reforms",
        "Inequality",
        "Political Stability",
        "Debt Sustainability",
        "Other",
    ],
}

# Map notebook sector prefix to sector name
PREFIX_TO_SECTOR = {"mon": "Monetary", "fis": "Fiscal"}


def _load_cache(cache_path: Path) -> dict[str, dict[str, str]]:
    if cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict[str, dict[str, str]], cache_path: Path) -> None:
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def _classify_via_llm(
    areas: list[str],
    sector: str,
    model: str = "gpt-5.4-mini",
) -> dict[str, str]:
    """Call OpenAI to classify a batch of area labels into sector categories."""
    from dotenv import load_dotenv
    load_dotenv(_REPO_ROOT / ".env")

    from openai import OpenAI
    client = OpenAI()

    categories = SECTOR_CATEGORIES[sector]
    cat_list = "\n".join(f"  {i+1}. {c}" for i, c in enumerate(categories))
    area_list = "\n".join(f"  {i+1}. {a}" for i, a in enumerate(areas))

    prompt = f"""You are classifying IMF Article IV report disagreement area labels into predefined higher-level categories.

Sector: {sector}
Available categories (pick exactly one per label):
{cat_list}

Rules:
- For each area label below, return the single best-matching category name from the list above.
- Use the exact category name as written above.
- If none of the specific categories fits well, return "Other".

Area labels to classify:
{area_list}

Return a JSON object with a "classifications" array. Each element has "area" (the original label) and "category" (the chosen category name)."""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
    )

    raw = response.choices[0].message.content
    parsed = json.loads(raw)
    classifications = parsed.get("classifications", [])
    result = {}
    valid_cats = set(categories)
    for item in classifications:
        area = item.get("area", "").lower().strip()
        cat = item.get("category", "Other")
        if cat not in valid_cats:
            cat = "Other"
        result[area] = cat
    return result


def classify_areas_batch(
    areas: Sequence[str],
    sector: str,
    *,
    cache_path: Path | None = None,
    model: str = "gpt-5.4-mini",
    batch_size: int = 80,
) -> dict[str, str]:
    """Classify area labels into higher-level categories for the given sector.

    Returns a dict mapping each lowercase area label to its category name.
    Uses a persistent JSON cache — only uncached labels trigger LLM calls.
    """
    if cache_path is None:
        cache_path = DEFAULT_CACHE_PATH

    if sector not in SECTOR_CATEGORIES:
        raise ValueError(f"Unknown sector {sector!r}. Valid: {list(SECTOR_CATEGORIES)}")

    cache = _load_cache(cache_path)
    sector_cache = cache.setdefault(sector, {})

    normalized = [a.lower().strip() for a in areas if a and str(a).strip()]
    unique = list(set(normalized))
    uncached = [a for a in unique if a not in sector_cache]

    if uncached:
        print(f"  [classify] {sector}: {len(uncached)} new labels to classify "
              f"({len(unique) - len(uncached)} cached)")
        for i in range(0, len(uncached), batch_size):
            batch = uncached[i : i + batch_size]
            result = _classify_via_llm(batch, sector, model=model)
            sector_cache.update(result)
            for a in batch:
                if a not in sector_cache:
                    sector_cache[a] = "Other"
        _save_cache(cache, cache_path)

    return {a: sector_cache.get(a, "Other") for a in normalized}


def preseed_cache_from_field_dicts(cache_path: Path | None = None) -> None:
    """Populate the cache with all known mappings from the reference notebook."""
    if cache_path is None:
        cache_path = DEFAULT_CACHE_PATH

    ref_notebook = _TRACTION_DIR / "temp" / "reference_code" / "14.analysis_full_sample.ipynb"
    if not ref_notebook.exists():
        print(f"WARNING: Reference notebook not found at {ref_notebook}")
        return

    import json as _json
    with open(ref_notebook) as f:
        nb = _json.load(f)

    sector_cells = {
        24: "Monetary",
        26: "Fiscal",
        28: "External",
        30: "Financial",
        32: "Real",
    }

    cache = _load_cache(cache_path)

    for cell_idx, sector_name in sector_cells.items():
        src = "".join(nb["cells"][cell_idx]["source"])
        local_ns: dict = {}
        try:
            exec(src, {}, local_ns)
        except Exception as e:
            print(f"  WARNING: Could not parse cell {cell_idx} ({sector_name}): {e}")
            continue
        if "field_dict" not in local_ns:
            continue
        fd = local_ns["field_dict"]
        sector_cache = cache.setdefault(sector_name, {})
        count = 0
        for category, labels in fd.items():
            for label in labels:
                key = label.lower().strip()
                if key not in sector_cache:
                    sector_cache[key] = category
                    count += 1
        print(f"  {sector_name}: added {count} labels ({len(sector_cache)} total)")

    _save_cache(cache, cache_path)
    print(f"  Cache saved to {cache_path}")


def _extract_areas_from_general_csv(
    data_path: Path,
) -> dict[str, list[str]]:
    """Extract unique area labels per sector from a general-agreement CSV.

    Handles both archive format ({area: severity} dict) and incremental format
    ([{area: ..., severity: ...}] list of dicts).
    """
    df = pd.read_csv(data_path)

    archive_cols = {
        "Monetary_gpt": "Monetary",
        "Fiscal_gpt": "Fiscal",
        "External_gpt": "External",
        "Financial_gpt": "Financial",
        "Real_gpt": "Real",
        "other_areas_gpt": "Other",
    }
    # Both v1 (`other_areas`) and v2 (`Other_Sector`) shapes route to the
    # `Other` sector so the same category list classifies either column.
    incremental_cols = {
        "Monetary_Sector": "Monetary",
        "Fiscal_Sector": "Fiscal",
        "External_Sector": "External",
        "Financial_Sector": "Financial",
        "Real_Sector": "Real",
        "Other_Sector": "Other",
        "other_areas": "Other",
    }

    col_map = {}
    for col, sector in archive_cols.items():
        if col in df.columns:
            col_map[col] = sector
    for col, sector in incremental_cols.items():
        if col in df.columns and sector not in col_map.values():
            col_map[col] = sector

    result: dict[str, list[str]] = {}
    for col, sector in col_map.items():
        areas: list[str] = []
        for v in df[col].dropna():
            try:
                parsed = ast.literal_eval(v) if isinstance(v, str) else v
            except (ValueError, SyntaxError):
                continue
            if isinstance(parsed, dict):
                areas.extend(parsed.keys())
            elif isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and "area" in item:
                        areas.append(item["area"])
                    elif isinstance(item, str):
                        areas.append(item)
        result[sector] = list(set(a.lower().strip() for a in areas if a))
    return result


def classify_general_csv(
    data_path: Path,
    *,
    cache_path: Path | None = None,
    model: str = "gpt-5.4-mini",
) -> dict[str, dict[str, str]]:
    """Classify all disagreement areas in a general-agreement CSV file.

    Returns {sector: {area: category, ...}} for all sectors found.
    """
    sector_areas = _extract_areas_from_general_csv(data_path)
    results = {}
    for sector, areas in sector_areas.items():
        if not areas:
            continue
        if sector not in SECTOR_CATEGORIES:
            print(f"  WARNING: Unknown sector {sector!r}, skipping")
            continue
        mapping = classify_areas_batch(areas, sector, cache_path=cache_path, model=model)
        results[sector] = mapping
        print(f"  {sector}: {len(mapping)} areas classified")
    return results


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Classify IMF Article IV disagreement area labels."
    )
    parser.add_argument("--preseed", action="store_true",
                        help="Pre-seed cache from reference notebook field_dict entries")
    parser.add_argument("--data-file", type=Path,
                        help="General-agreement CSV to classify areas from")
    parser.add_argument("--sector", type=str,
                        help="Sector name (for --areas mode)")
    parser.add_argument("--areas", nargs="+",
                        help="Area labels to classify (requires --sector)")
    parser.add_argument("--cache-file", type=Path, default=DEFAULT_CACHE_PATH)
    parser.add_argument("--model", type=str, default="gpt-5.4-mini")
    args = parser.parse_args()

    if args.preseed:
        preseed_cache_from_field_dicts(cache_path=args.cache_file)

    if args.data_file:
        results = classify_general_csv(
            args.data_file, cache_path=args.cache_file, model=args.model
        )
        print(f"\nClassified {sum(len(v) for v in results.values())} total areas")

    if args.sector and args.areas:
        mapping = classify_areas_batch(
            args.areas, args.sector, cache_path=args.cache_file, model=args.model
        )
        for area, cat in mapping.items():
            print(f"  {area!r} -> {cat}")

    if not (args.preseed or args.data_file or (args.sector and args.areas)):
        parser.print_help()


if __name__ == "__main__":
    main()
