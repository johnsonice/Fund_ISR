#!/usr/bin/env bash
# Ad-hoc: run the zero-shot general (cross-sector) agreement inference TEN times
# over the SAME input, into fresh `general_agreement_repeat10/v1..v10/` folders,
# for a model-randomness / reproducibility study.
#
# Why ten identical runs:
#   - gpt-5.4-mini-2026-03-17 is a reasoning model: temperature is pinned to 1.0
#     and `seed` is not supported, so the per-document integer scores are NOT
#     reproducible across runs. Repeating the exact same job N times lets you
#     measure that run-to-run variance directly (spread of Agreement_* scores
#     per document across v1..v10).
#
# Recipe (inference_general_agreement.py defaults = the v2 recipe):
#   model=gpt-5.4-mini-2026-03-17, prompt-variant=simple_v2, temperature=1.0,
#   max-output-tokens=16384. Passed implicitly by not overriding them.
#
# Input:  incremental_update/06_07_2026_update/df_documents_general_merged.csv
#         (1280 docs, all with both staff & buff text; the script's own
#         Agreement_* / *_Sector columns in that file are ignored and rescored.)
# Output: output/adhoc/general_agreement_repeat10/
#           v{1..10}/
#             general_agreement_v{i}.jsonl          (batch request, 1280 lines)
#             batch_results_batch_*.jsonl           (raw batch responses)
#             df_documents_general_v{i}.csv         (post-processed, 1280 rows)
#           repeat10_v{i}_<stamp>.log               (per-rep stdout/stderr)
#
# Scheduling: all 10 batches are submitted in parallel (one background process
# per rep). Each process submits its own OpenAI Batch job, then blocks polling
# its own batch to completion and post-processes — so the 10 jobs run
# concurrently on OpenAI's side. This wrapper waits for all 10 and reports which
# reps succeeded / failed.
#
# GUARD: submitting 10 full batches (12,800 requests total) costs money, so the
# full run only fires with --yes (or CONFIRM=1). Without it, the wrapper runs a
# single small --test-mode smoke check (3 rows, 1 batch) and stops, so you can
# validate the model id / paths / schema before scaling up.
#
# Usage:
#   bash run_general_agreement_repeat10.sh            # smoke test only (3 rows), then stop
#   bash run_general_agreement_repeat10.sh --yes      # full run: 10 parallel batches x 1280 rows
set -euo pipefail

cd /data/home/xiong/dev/Fund_ISR/src/Traction/
eval "$(conda shell.bash hook 2>/dev/null)" && conda activate traction 2>/dev/null || true

# Pin the traction python so the script works even when conda activation no-ops
# (e.g. when invoked from another env in CI/agent contexts).
TRACTION_PY="${TRACTION_PY:-/data/home/xiong/miniconda3/envs/traction/bin/python}"
if [ ! -x "$TRACTION_PY" ]; then
  echo "ERROR: traction python not found at $TRACTION_PY" >&2
  echo "Set TRACTION_PY=/path/to/traction/bin/python or fix conda activation." >&2
  exit 1
fi

OUTPUT_BASE="${OUTPUT_BASE:-/data/home/xiong/data/Fund/CSR/Tractions/output}"
DATA_FILE="${DATA_FILE:-${OUTPUT_BASE}/incremental_update/06_07_2026_update/df_documents_general_merged.csv}"
OUTPUT_DIR="${OUTPUT_DIR:-${OUTPUT_BASE}/adhoc/general_agreement_repeat10}"
N_REPS="${N_REPS:-10}"

# --- Arg parsing: --yes / CONFIRM=1 gates the full (money-spending) run --------
CONFIRM="${CONFIRM:-0}"
while [ $# -gt 0 ]; do
  case "$1" in
    --yes|-y)  CONFIRM=1; shift ;;
    -h|--help) sed -n '2,50p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [ ! -f "$DATA_FILE" ]; then
  echo "ERROR: input data file not found: $DATA_FILE" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
STAMP="$("$TRACTION_PY" -c 'import datetime; print(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))')"

# --- Clean the input: strip pre-existing scoring columns -----------------------
# NOTE: the original DATA_FILE is treated as strictly READ-ONLY — it is never
# written to. df_documents_general_merged.csv already carries a prior run's
# Agreement_* / *_Sector columns. If we fed those straight in,
# _post_process_if_needed would merge this run's fresh columns onto
# identically-named old ones and pandas would suffix them _x (old) / _y (new),
# polluting the output schema. So we read the original and write a SEPARATE
# cleaned copy (INPUT_FILE) keeping only the base columns (same schema as
# df_documents.csv), and point all reps at that copy.
INPUT_FILE="${OUTPUT_DIR}/_input_clean.csv"
"$TRACTION_PY" - "$DATA_FILE" "$INPUT_FILE" <<'PY'
import sys, pandas as pd
src, dst = sys.argv[1], sys.argv[2]
df = pd.read_csv(src, low_memory=False)
drop = [c for c in df.columns if c.startswith('Agreement_') or c.endswith('_Sector') or c == 'id']
df.drop(columns=drop, errors='ignore').to_csv(dst, index=False)
print(f"Cleaned input: dropped {len(drop)} scoring cols -> {dst} ({len(df)} rows, cols: {list(df.drop(columns=drop, errors='ignore').columns)})")
PY

echo "=== General Agreement — repeat x${N_REPS} (model-randomness study) ==="
echo "Source (read-only): $DATA_FILE"
echo "Cleaned input     : $INPUT_FILE"
echo "Output: $OUTPUT_DIR/v{1..${N_REPS}}/df_documents_general_v{i}.csv"
echo "Config: model / prompt-variant simple_v2 / temperature 1.0 / max-output-tokens 16384 (script defaults)"
echo "Python: $TRACTION_PY"
echo

# --- Smoke test (safe default) -------------------------------------------------
if [ "$CONFIRM" != "1" ]; then
  SMOKE_DIR="${OUTPUT_DIR}/_smoke_${STAMP}"
  mkdir -p "$SMOKE_DIR"
  echo ">>> SMOKE TEST (no --yes): 1 batch of 3 sampled rows -> ${SMOKE_DIR}"
  echo ">>> This submits ONE small OpenAI batch to validate model id / paths / schema."
  echo
  "$TRACTION_PY" inference_general_agreement.py \
    --data-file  "${INPUT_FILE}" \
    --output-dir "${SMOKE_DIR}" \
    --output-file "df_documents_general_smoke.csv" \
    --jsonl-file "general_agreement_smoke.jsonl" \
    --test-mode --sample-size 3 \
    --submit --post-process
  echo
  echo ">>> Smoke test done. Inspect ${SMOKE_DIR}/df_documents_general_smoke.csv"
  echo ">>> If the Agreement_* columns look sane, re-run with --yes to fire all ${N_REPS} parallel batches."
  exit 0
fi

# --- Full run: N parallel reps -------------------------------------------------
echo ">>> FULL RUN: submitting ${N_REPS} batches in parallel ..."
declare -a PIDS=()
declare -a REP_LOGS=()

for i in $(seq 1 "$N_REPS"); do
  REP_DIR="${OUTPUT_DIR}/v${i}"
  REP_LOG="${OUTPUT_DIR}/repeat10_v${i}_${STAMP}.log"
  mkdir -p "$REP_DIR"
  REP_LOGS[$i]="$REP_LOG"
  echo "  rep v${i}: output -> ${REP_DIR}  | log -> ${REP_LOG}"
  (
    "$TRACTION_PY" inference_general_agreement.py \
      --data-file  "${INPUT_FILE}" \
      --output-dir "${REP_DIR}" \
      --output-file "df_documents_general_v${i}.csv" \
      --jsonl-file "general_agreement_v${i}.jsonl" \
      --submit --post-process
  ) > "${REP_LOG}" 2>&1 &
  PIDS[$i]=$!
done

echo
echo ">>> All ${N_REPS} reps launched. Waiting for completion (each polls its own batch)..."

FAILED=0
for i in $(seq 1 "$N_REPS"); do
  if wait "${PIDS[$i]}"; then
    echo "  [OK]   rep v${i} (pid ${PIDS[$i]})"
  else
    rc=$?
    echo "  [FAIL] rep v${i} (pid ${PIDS[$i]}) exit=${rc} — see ${REP_LOGS[$i]}" >&2
    FAILED=$((FAILED + 1))
  fi
done

echo
if [ "$FAILED" -ne 0 ]; then
  echo "DONE with ${FAILED}/${N_REPS} reps FAILED. Check the per-rep logs above." >&2
  exit 1
fi
echo "DONE. All ${N_REPS} reps succeeded. Outputs:"
for i in $(seq 1 "$N_REPS"); do
  echo "  ${OUTPUT_DIR}/v${i}/df_documents_general_v${i}.csv"
done
