# Chain-Base Audit Report: `06_07_2026_update`

## 1. Executive Summary

**The chain base is NOT ready to freeze as-is. Patch first.** There is one real, forward-propagating gap that will otherwise contaminate every future incremental update: **13 genuine 2025/2026 Article IV Consultations were never populated with report text and therefore never reached core, general, or any scored artifact.** Because step 08 auto-chains onto this directory, these 13 holes become permanent.

The good news: the damage is **contained and well-understood**. All other apparent gaps are either benign-by-design (currency unions, CEMAC un-scoreable, AIV/schema distinctions) or low-severity data-consistency nits recoverable by a cheap splice. The one expensive item (12 docs needing re-scrape + re-inference) is small (0.8% of the backbone) but must be fixed here rather than deferred, or it propagates.

**Two corrections to the working hypotheses you were carrying in:** the real propagating gap is **13, not 14** (Brunei `9798229003162` is a procedural cycle-change proposal with no bilateral text — legitimately non-scoreable), and the 5 "staff-only docs with bilateral scores" are an expected paragraph-file condition, not a core defect worth blocking on.

---

## 2. Confirmed Real Gaps (most impactful first)

| # | File(s) | What | Scope | Recoverable w/o inference? | Recovery path |
|---|---------|------|-------|----------------------------|---------------|
| 1 | intermediate + df_aiv + df_paragraphs + core + general | **12 TOC-only Article IV docs** never scraped. Only `issue_toc.html` (nav/boilerplate) on disk; `article-A00X-en.html` body files were never downloaded → empty text_staff/buff → no paragraphs → absent from every scored artifact. `parse_status='success'` is a false signal. | 12 of 1453 (0.8%). ISBNs: 9798229006811 (Japan '25), 9798229046374 (Dominica), 9798229046381 (Spain), 9798229046831 (Argentina), 9798229047258 (Peru), 9798229047340 (Greece), 9798229047586 (HK SAR), 9798229048446 (Azerbaijan), 9798229048538 (Trinidad), 9798229048651 (Costa Rica), 9798229048965 (Fiji), 9798229050456 (Seychelles) | **NO** — text absent from all backups + prior 05252026 run. Requires re-scrape **then** full re-inference | Re-crawl each `article-A00X-en.html` from IMF eLibrary (source URLs are embedded in each `issue_toc.html`, all under `elibrary.imf.org/view/journals/002/`), then re-run: XML→text parse → paragraphs → topic/sector classification (step 04) → `document_by_type_sector` (step 05) → 4 fine-tuned inferences (agreement/stance × monetary/fiscal) → zero-shot general → re-chain |
| 2 | df_aiv + df_paragraphs + intermediate | **Montenegro 9798229030076 parse-to-frame bug.** Full staff-report body IS on disk (`article-A000/A001/A002-en.html`, ~260K chars, `parse_status=success`, `fallback_used=True`) yet text_staff/buff/sa are empty — a genuine extractor bug that silently emptied a multi-article package. | 1 of 1453 | **YES (partial)** — body files already on disk; no re-download | Re-run only the XML→text parse + coalesce over `ArticleIV_xml_updated/06_07_2026_update/imf_staff_reports_html_by_year_isbn/2025/9798229030076/`, then paragraphs → classification → inference for this one ISBN. **Still needs inference** (no scored artifact exists), but no scrape. Fix the extractor bug — it could silently empty other multi-article packages every cycle |
| 3 | df_documents_general | **4 rows: `Agreement_Other==99` (not-scored sentinel) with a non-empty `Other_Sector` disagreement list** — internal contradiction. Lineage-traced to the operator-labeled `wrongbase` generation being picked up instead of the consistent one. | 4 of 1280: Nepal '15 (9781513562247), Costa Rica '17 (9781484304532), HK SAR '16 (9781475566031), Belgium '15 (9781498355100) | **YES — cheap splice** | Copy the (Agreement_Other, Other_Sector) pair for these 4 ISBNs from `df_documents_general_merged.precoalesce.bak.csv` into the merged file. **Do NOT bulk-copy the column** (424 rows legitimately differ from a full re-gen). Verify: `(Agreement_Other=='99') & (Other_Sector.strip()!='[]')` → 0 rows. Do **not** chase `general_agreement_batch.jsonl` — these ISBNs aren't in it |
| 4 | df_aiv (backbone) | **Brunei 9798229003162 — carried-forward empty shell.** Metadata-only row, no source dir anywhere on disk (Windows OneDrive path only), `parse_status=NaN`. Entered in the 05252026 cycle and propagates forward. | 1 of 1453 | **NO** — but **no recovery needed**: it's a procedural "Stand-Alone Proposal to Move Brunei to a 24-Month Consultation Cycle," has_buff=0, non-scoreable by design. Low priority | Optional: re-fetch from eLibrary only if you want the backbone tidy. It can never yield a bilateral score. Use `publication_year=2025` (populated) for the blank Year-from-title. Safe to leave |

**Cross-cutting note for gap #1/#2:** fix the extractor's `parse_status` logic so a package whose only file is `issue_toc.html` (or whose body parse yields empty staff/buff) is flagged **failed/empty**, not `success`. This is the root cause of the silent, recurring gap class.

---

## 3. Looks Like a Gap but EXPECTED — Do Not Chase

- **Currency-union monetary nulls** (Euro area, ECCU, CEMAC, WAEMU): no Monetary Policy topic → monetary columns null is correct by design.
- **CEMAC 2017 (9781484305775) — 1 core doc not in general.** Has staff text but zero buff text → un-scoreable bilateral. This is exactly why core's monetary-null set (353) is one larger than general's `Agreement_Monetary==99` set (352). Correct by design.
- **9 staff-only docs (0 buff paragraphs) in df_paragraphs.** All 9 genuinely lack an authorities' (buff) document; this is the correct paragraph-file condition. *(Side note: 5 of them nonetheless carry fine-tuned bilateral scores in core — a real but separate, low-severity inference-stage anomaly to audit later, not a chain-base blocker. Also, `9781484383667` Mexico 2018 has a mislabeled `filename_buff` pointing at a staff-statement XML.)*
- **AIV flag consistency.** AIV=True ≡ `document_type=='issue'` (284 docs), zero per-doc inconsistencies. The 1011 AIV=nan docs containing "Article IV" in their title are an older schema/vintage, correctly NOT flagged. Blank country codes/years fall entirely within AIV=nan. No action.
- **Brunei** (see gap #4) — real backbone shell but non-scoreable; not worth blocking the freeze.

---

## 4. Prioritized Recommendations (before the next update)

**Do these in order. Distinguish cheap splice vs. expensive re-inference.**

1. **[CHEAP — splice, do first]** Fix the 4 contradictory `Agreement_Other` rows in `df_documents_general_merged.csv` by splicing the (Agreement_Other, Other_Sector) pair from `df_documents_general_merged.precoalesce.bak.csv` for the 4 ISBNs (9781513562247, 9781484304532, 9781475566031, 9781498355100). Per-row copy only. Verify `→ 0` contradictory rows. No inference.

2. **[MODERATE — re-parse on-disk + inference, no scrape]** Recover **Montenegro 9798229030076**: re-run the XML→text parse over the already-present `article-A00{0,1,2}-en.html`, then paragraphs → classification → 4 inferences → re-chain. Simultaneously **fix the extractor parse-to-frame bug** that emptied it (and the `parse_status='success'` false-flag logic).

3. **[EXPENSIVE — re-scrape + full re-inference]** Recover the **12 TOC-only docs**. For each ISBN, parse its `issue_toc.html` for the article links, re-crawl `article-A00X-en.html` from eLibrary (`journals/002/…`), then run the full chain: XML→text → paragraphs → topic/sector (step 04) → `document_by_type_sector` (step 05) → 4 fine-tuned inferences → zero-shot general → re-chain. This is the only item requiring both re-scrape and re-inference; it is unavoidable (zero scored data exists anywhere for these). Nothing is recoverable from the prior 05252026 run.

4. **[OPTIONAL / defer]** Brunei 9798229003162 — leave as-is (non-scoreable proposal doc) or re-fetch later purely for backbone tidiness. Does not block the freeze.

**Bottom line:** items 1–3 must land before you freeze this directory as the chain base. Item 1 is a 5-minute splice; item 2 is a bounded single-doc fix plus an extractor patch; item 3 is the real cost but is small (12 docs) and cannot be deferred without permanently baking the gap into all downstream updates.