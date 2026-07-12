"""HTML variant of extract_StaffAppraisal_and_Buff.

Mirrors the XML extractor in data_preprocess.py so that downstream code in
03_incremental_aiv_update_html.py can consume the same 10-tuple of dicts and
produce byte-shape-identical CSV outputs.

Tag mapping (XML JATS -> rendered IMF eLibrary HTML):
    <sec>          -> <div class="section ..." id="A00Xlev1sec[N]">
    <title>        -> <h2> (or <h3>) inside the section div
    <bold>         -> <strong>
    <p>            -> <p>
    <fig>          -> <div class="figure">, <figure>
    <table-wrap>   -> <div class="tableWrap ...">, <table>
    <boxed-text>   -> <div class="box">
    <article-title>-> <meta property="og:title"> content
"""
from __future__ import annotations

import re
from copy import copy
from pathlib import Path

import bs4 as bs
from bs4 import BeautifulSoup
from tqdm import tqdm

_PARSER = "html.parser"

_AUTH_MARKER_SET = {"authorities views", "authorities view"}


def _norm(s: str) -> str:
    return " ".join((s or "").split()).strip()


def _norm_lower(s: str) -> str:
    return _norm(s).lower().replace("’", "").replace("'", "")


def _strip_non_narrative(scope) -> None:
    """In-place removal of non-narrative elements: figures, tables, boxes,
    footnotes, and in-text footnote-reference <sup> wrappers.
    """
    if scope is None:
        return

    for tag in scope.find_all("figure"):
        tag.decompose()
    for tag in scope.find_all("div", class_=lambda c: c and "figure" in c.split()):
        tag.decompose()

    for tag in scope.find_all("table"):
        tag.decompose()
    for tag in scope.find_all("div", class_=lambda c: c and any(cls.startswith("tableWrap") for cls in c.split())):
        tag.decompose()

    for tag in scope.find_all("div", class_=lambda c: c and "box" in c.split()):
        tag.decompose()
    for tag in scope.find_all(["label", "aside"]):
        tag.decompose()

    for tag in scope.find_all("div", class_=lambda c: c and ("footnote" in c.split() or "footnoteGroup" in c.split())):
        tag.decompose()

    for sup in list(scope.find_all("sup")):
        a = sup.find("a", id=lambda i: isinstance(i, str) and i.startswith("RA"))
        if a is not None:
            sup.decompose()


def _section_title(section_div) -> str:
    h = section_div.find(["h2", "h3", "h4"], recursive=False)
    if h is None:
        h = section_div.find(["h2", "h3", "h4"])
    return h.get_text(" ", strip=True) if h else ""


def _direct_paragraphs(section_div) -> list:
    """Paragraphs that belong directly to this section (not to a nested section).

    A <p> belongs to this section if its nearest ancestor with class "section"
    is the section_div itself.
    """
    out = []
    for p in section_div.find_all("p"):
        parent_sec = p.find_parent(
            "div",
            class_=lambda c: c and "section" in c.split(),
        )
        if parent_sec is section_div:
            out.append(p)
    return out


def _flatten_sections(article_body) -> list[tuple[str, list]]:
    """Return a flat list of (title, paragraphs) leaves from articleBody.

    Mirrors the XML extractor's leaf-flattening behavior: nested sections are
    treated as their own leaves; if the parent has any residual paragraphs that
    don't belong to a nested section, those become a leaf too.
    """
    if article_body is None:
        return []

    top_sections = [
        div
        for div in article_body.find_all("div", class_=lambda c: c and "section" in c.split(), recursive=False)
    ]
    if not top_sections:
        top_sections = article_body.find_all("div", class_=lambda c: c and "section" in c.split())

    leaves: list[tuple[str, list]] = []

    def _walk(section_div):
        nested = [
            d
            for d in section_div.find_all("div", class_=lambda c: c and "section" in c.split())
            if d.find_parent(
                "div", class_=lambda c: c and "section" in c.split()
            )
            is section_div
        ]
        own_paras = _direct_paragraphs(section_div)
        if nested:
            if own_paras:
                leaves.append((_section_title(section_div), own_paras))
            for child in nested:
                _walk(child)
        else:
            leaves.append((_section_title(section_div), section_div.find_all("p")))

    for s in top_sections:
        _walk(s)
    return leaves


def _find_staff_report_html(package_dir: Path) -> Path | None:
    """Pick the article file containing a Staff Appraisal heading.

    Falls back to the richest-narrative article body when NO article carries a
    Staff-Appraisal heading — some reports (e.g. Montenegro 2025) structure the
    staff report as Context/Recent Developments/Outlook/Policy Discussions/Annexes
    with no separately-titled appraisal section. Without this fallback such a
    package extracts to nothing and is silently dropped. The fallback only
    triggers when the primary (heading-based) search finds nothing, so it never
    changes the selection for any report that does have an appraisal heading.
    """
    pattern = re.compile(r"^article-A00\d(-[a-z]{2})?\.html$", re.IGNORECASE)
    candidates = sorted(
        p
        for p in package_dir.iterdir()
        if p.is_file()
        and pattern.match(p.name)
        and not p.stem.lower().startswith("article-a000")
    )
    fallback: Path | None = None
    fallback_score = 0
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        soup = BeautifulSoup(text, _PARSER)
        body = soup.find("div", id="articleBody")
        if body is None:
            continue
        for h in body.find_all(["h2", "h3", "h4"]):
            t = _norm_lower(h.get_text(" ", strip=True))
            if "staff appraisal" in t or "staff apraisal" in t or "staff assessment" in t:
                return path
        # Track the article with the most numbered narrative paragraphs as the
        # fallback staff-report body (the real report, not a title/annex-only file).
        numbered = sum(
            1 for p in body.find_all("p")
            if p.get_text(strip=True) and p.get_text(strip=True)[0].isdigit()
        )
        if numbered > fallback_score:
            fallback_score, fallback = numbered, path
    # Require a meaningful body so we don't select a stub (e.g. a title-page-only
    # A002). 10 numbered paragraphs is well below any real staff report.
    if fallback is not None and fallback_score >= 10:
        return fallback
    return None


def _buff_title_from_meta(soup) -> str:
    m = soup.find("meta", attrs={"property": "og:title"})
    if m and m.get("content"):
        return m["content"]
    h1 = soup.find("h1")
    return h1.get_text(" ", strip=True) if h1 else ""


def _find_buff_html(package_dir: Path, staff_path: Path | None) -> Path | None:
    pattern = re.compile(r"^article-A00\d(-[a-z]{2})?\.html$", re.IGNORECASE)
    candidates = sorted(
        [
            p
            for p in package_dir.iterdir()
            if p.is_file()
            and pattern.match(p.name)
            and not p.stem.lower().startswith("article-a000")
            and (staff_path is None or p != staff_path)
        ],
        reverse=True,
    )
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        soup = BeautifulSoup(text, _PARSER)
        title = _buff_title_from_meta(soup).lower()
        if "statement by" in title or "statement on" in title:
            return path
        body = soup.find("div", id="articleBody")
        if body is not None:
            for p in body.find_all("p"):
                if p.get_text(" ", strip=True).lower().startswith("statement by"):
                    return path
    return None


def _strong_text(p) -> str:
    s = p.find("strong")
    if s is None:
        s = p.find("b")
    return _norm_lower(s.get_text(" ", strip=True)) if s else ""


def _p_text(p) -> str:
    return _norm_lower(p.get_text(" ", strip=True))


def _scrub_for_text(p_tag):
    """Return a deep copy of <p> with footnote markers stripped, suitable for text extraction."""
    p_copy = copy(p_tag)
    for sup in list(p_copy.find_all("sup")):
        a = sup.find("a", id=lambda i: isinstance(i, str) and i.startswith("RA"))
        if a is not None:
            sup.decompose()
    return p_copy


def _para_text(p) -> str:
    return _scrub_for_text(p).get_text(" ", strip=True)


def _find_sa_section_div(inner):
    """Locate the section div whose own heading reads "Staff Appraisal" (or typo).

    Searches all `<div class="section">` (any depth) and picks the one whose
    own h2/h3/h4 title — not a descendant's — matches.
    """
    for div in inner.find_all("div", class_=lambda c: c and "section" in c.split()):
        title = _section_title(div)
        t = _norm_lower(title)
        if "staff appraisal" in t or "staff apraisal" in t or "staff assessment" in t:
            return div
    return None


def _build_sr_sections(article_body):
    """Walk article_body once, returning (sr_leaves, sa_section_div, body_copy).

    sr_leaves is a list of (title, [<p>...]) from sections that come BEFORE the
    Staff Appraisal section in document order. The SA section itself and any
    sections that come after it (Annexes, etc.) are excluded.
    """
    body_copy = BeautifulSoup(str(article_body), _PARSER)
    _strip_non_narrative(body_copy)

    inner = body_copy.find("div", id="articleBody")
    if inner is None:
        inner = body_copy

    sa_section_div = _find_sa_section_div(inner)
    if sa_section_div is None:
        # No Staff-Appraisal section (some reports don't title one). Rather than
        # drop the whole document, keep ALL narrative sections as SR leaves so the
        # staff/authority split still runs; SA is simply empty for this report.
        all_leaves = [(title, paras) for title, paras in _flatten_sections(inner) if paras]
        return all_leaves, None, body_copy

    leaves = _flatten_sections(inner)
    sa_descendant_ids = {id(sa_section_div)}
    sa_descendant_ids.update(id(d) for d in sa_section_div.find_all("div", class_=lambda c: c and "section" in c.split()))

    sr_leaves: list[tuple[str, list]] = []
    sa_position = None
    leaf_section_divs = list(inner.find_all("div", class_=lambda c: c and "section" in c.split()))
    for div in leaf_section_divs:
        if id(div) == id(sa_section_div):
            sa_position = leaf_section_divs.index(div)
            break

    leaves_kept: list[tuple[str, list]] = []
    seen_sa = False
    for title, paras in leaves:
        if not paras:
            continue
        owner = paras[0].find_parent(
            "div", class_=lambda c: c and "section" in c.split()
        )
        if owner is None:
            continue
        if id(owner) in sa_descendant_ids:
            seen_sa = True
            continue
        if seen_sa:
            continue
        leaves_kept.append((title, paras))
    return leaves_kept, sa_section_div, body_copy


def _extract_sa(sa_section_div) -> tuple[str, list[str]]:
    if sa_section_div is None:
        return "", []
    sa_scope = BeautifulSoup(str(sa_section_div), _PARSER)
    _strip_non_narrative(sa_scope)

    ps = sa_scope.find_all("p")
    numbered = [p for p in ps if p.get_text(strip=True) and p.get_text(strip=True)[0].isdigit()]
    if numbered:
        last = numbered[-1]
        last_str = str(last)
        full_str = str(sa_scope)
        cut = full_str.find(last_str)
        if cut >= 0:
            truncated = full_str[: cut + len(last_str)]
            sa_scope = BeautifulSoup(truncated, _PARSER)

    paras = [_para_text(p) for p in sa_scope.find_all("p")]
    list_items = []
    for lst in sa_scope.find_all(["ul", "ol"]):
        for line in lst.get_text("\n").split("\n"):
            if line.strip():
                list_items.append(line.strip())
    paras = [p for p in paras if p] + list_items
    return str(sa_scope), paras


def _split_sr_av(sr_leaves) -> tuple[list[str], list[str], bool]:
    """Apply the 4-rule heuristic, returning (staff_paragraphs, authority_paragraphs, av_uncertain)."""
    if not sr_leaves:
        return [], [], True

    if any("authorit" in _norm_lower(title) for title, _ps in sr_leaves):
        rule_type = 0
    elif any(
        _strong_text(p).startswith("authorit") and _p_text(p) not in _AUTH_MARKER_SET
        for _t, ps in sr_leaves
        for p in ps
    ):
        rule_type = 1
    elif any(
        p.find("strong") is not None and _p_text(p) in _AUTH_MARKER_SET
        for _t, ps in sr_leaves
        for p in ps
    ):
        rule_type = 3
    else:
        rule_type = 2

    staff_l = []
    authority_l = []

    if rule_type == 0:
        for title, ps in sr_leaves:
            if "authorit" in _norm_lower(title):
                authority_l += ps
            else:
                staff_l += ps
    elif rule_type == 1:
        for _title, ps in sr_leaves:
            for p in ps:
                if _strong_text(p).startswith("authorit"):
                    authority_l.append(p)
                else:
                    staff_l.append(p)
    elif rule_type == 3:
        for _title, ps in sr_leaves:
            if not ps:
                continue
            already_auth = set()
            for idx, p in enumerate(ps):
                if p.find("strong") is not None and _p_text(p) in _AUTH_MARKER_SET:
                    if idx + 1 < len(ps):
                        authority_l.append(ps[idx + 1])
                        already_auth.add(id(ps[idx + 1]))
            for p in ps:
                if id(p) in already_auth:
                    continue
                if p.find("strong") is not None and _p_text(p) in _AUTH_MARKER_SET:
                    continue
                staff_l.append(p)
    else:
        for _title, ps in sr_leaves:
            if not ps:
                continue
            staff_l += ps[:-1]
            last = ps[-1]
            if _strong_text(last) and "authorit" in _strong_text(last):
                authority_l.append(last)
            else:
                staff_l.append(last)

    para_sr = [t for t in (_para_text(p) for p in staff_l) if t]
    para_av = [t for t in (_para_text(p) for p in authority_l) if t]
    return para_sr, para_av, rule_type == 2


def _extract_buff(buff_path: Path) -> tuple[str, list[str]]:
    text = buff_path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(text, _PARSER)
    body = soup.find("div", id="articleBody")
    if body is None:
        return text, []

    _strip_non_narrative(body)

    og_title = _buff_title_from_meta(soup).lower()
    matched_by_meta = "statement by" in og_title or "statement on" in og_title

    if matched_by_meta:
        paras = [_para_text(p) for p in body.find_all("p")]
    else:
        marker = None
        for p in body.find_all("p"):
            if p.get_text(" ", strip=True).lower().startswith("statement by"):
                marker = p
                break
        if marker is None:
            return text, []
        paras = [_para_text(p) for p in marker.find_all_next("p")]
    paras = [p for p in paras if p.strip()]
    return text, paras


def extract_StaffAppraisal_and_Buff_html(folder_dict: dict[str, str]):
    """HTML variant of the XML extractor in data_preprocess.py.

    Parameters
    ----------
    folder_dict : dict[str, str]
        Maps package id (ISBN) to absolute path of the per-ISBN folder containing
        article-A00N-en.html files.

    Returns
    -------
    Tuple of 10 dicts with the same shape as the XML extractor:
        (staff_dict, staff_content_dict, text_sa_dict, para_sa_dict,
         buff_dict, buff_content_dict, para_bu_dict,
         para_sr_dict, para_av_dict, av_uncertain_dict)
    """
    staff_dict: dict[str, str] = {}
    staff_content_dict: dict[str, str] = {}
    text_sa_dict: dict[str, str] = {}
    para_sa_dict: dict[str, list[str]] = {}
    buff_dict: dict[str, str] = {}
    buff_content_dict: dict[str, str] = {}
    para_bu_dict: dict[str, list[str]] = {}
    para_sr_dict: dict[str, list[str]] = {}
    para_av_dict: dict[str, list[str]] = {}
    av_uncertain_dict: dict[str, bool] = {}

    for folder, package_path in tqdm(
        folder_dict.items(), desc="Extracting staff appraisal and buff statement (HTML)"
    ):
        package_dir = Path(package_path)
        if not package_dir.is_dir():
            continue

        staff_path = None
        try:
            staff_path = _find_staff_report_html(package_dir)
            if staff_path is not None:
                text = staff_path.read_text(encoding="utf-8", errors="replace")
                soup = BeautifulSoup(text, _PARSER)
                article_body = soup.find("div", id="articleBody")

                sr_leaves, sa_section_div, _scrubbed_body = _build_sr_sections(article_body)
                # Write whenever we have EITHER an appraisal section OR narrative SR
                # leaves. The old guard required sa_section_div, so appraisal-less
                # reports (sr_leaves present, SA None) were silently dropped.
                if sa_section_div is not None or sr_leaves:
                    sa_html, para_sa = _extract_sa(sa_section_div)  # ("", []) when None
                    staff_dict[folder] = str(staff_path)
                    staff_content_dict[folder] = text
                    text_sa_dict[folder] = sa_html
                    para_sa_dict[folder] = para_sa

                    para_sr, para_av, av_uncertain = _split_sr_av(sr_leaves)
                    para_sr_dict[folder] = para_sr
                    para_av_dict[folder] = para_av
                    av_uncertain_dict[folder] = av_uncertain
        except Exception:
            para_sr_dict.setdefault(folder, [])
            para_av_dict.setdefault(folder, [])
            av_uncertain_dict.setdefault(folder, True)

        try:
            buff_path = _find_buff_html(package_dir, staff_path)
            if buff_path is not None:
                buff_text, para_bu = _extract_buff(buff_path)
                if para_bu:
                    buff_dict[folder] = str(buff_path)
                    buff_content_dict[folder] = buff_text
                    para_bu_dict[folder] = para_bu
        except Exception:
            pass

    return (
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
    )
