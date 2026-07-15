#!/usr/bin/env bash
# Ad-hoc, trackable wrapper for patching the general-agreement gap docs.
#
# Runs the three phases of the top-up in order, each announced with a banner,
# checkpointed, and tee'd to a timestamped log so the whole process is auditable:
#
#   1. build-input : assemble the 37 scoreable missing-doc rows        (no API)
#   2. inference   : zero-shot general-agreement (v2) via Batch API    (HITS API)
#   3. append      : concat the results into df_documents_general_v2   (no API)
#
# The API-hitting step (2) is GUARDED: it only runs if you pass --yes (or set
# CONFIRM=1). Without it the wrapper stops after build-input so you can review
# the prepared input first — matching the "prepare only, stop before batch" flow.
#
# Usage:
#   bash patch_missing_general_agreement.sh                 # phase 1 only, then stop (safe default)
#   bash patch_missing_general_agreement.sh --yes           # phases 1 -> 2 -> 3 (submits the batch)
#   bash patch_missing_general_agreement.sh --from append   # resume at phase 3 (after batch done)
#
# Flags:
#   --yes           confirm the API-hitting inference step (else it is skipped)
#   --from PHASE    start at build-input | inference | append (default: build-input)
#   --model NAME    override the inference model (default: gpt-5.4-mini-2026-03-17)
set -euo pipefail

# ----------------------------------------------------------------------------
# Paths & config
# ----------------------------------------------------------------------------
THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRACTION_DIR="$(cd "${THIS_DIR}/../.." && pwd)"          # .../src/Traction
PY_SCRIPT="${THIS_DIR}/patch_missing_general_agreement.py"
INFER_SCRIPT="${TRACTION_DIR}/inference_general_agreement.py"

OUTPUT_ROOT="/data/home/xiong/data/Fund/CSR/Tractions/output"
ADHOC_DIR="${OUTPUT_ROOT}/adhoc/general_agreement_v2"
INPUT_CSV="${ADHOC_DIR}/df_documents_missing_input.csv"
PATCH_CSV="${ADHOC_DIR}/df_documents_general_v2_patch.csv"
TARGET_CSV="${ADHOC_DIR}/df_documents_general_v2.csv"

MODEL="${MODEL:-gpt-5.4-mini-2026-03-17}"
PROMPT_VARIANT="simple_v2"
MAX_OUTPUT_TOKENS=16384

# Resolve traction env's python explicitly — `conda activate` can silently no-op
# when another env is already active (agent/CI contexts), and this pipeline needs
# traction-only packages (openai SDK, python-dotenv, pydantic schemas).
TRACTION_PY="${TRACTION_PY:-/data/home/xiong/miniconda3/envs/traction/bin/python}"
if [ ! -x "$TRACTION_PY" ]; then
  echo "ERROR: traction python not found at $TRACTION_PY" >&2
  echo "Set TRACTION_PY=/path/to/traction/bin/python or fix conda activation." >&2
  exit 1
fi

# ----------------------------------------------------------------------------
# Arg parsing
# ----------------------------------------------------------------------------
CONFIRM="${CONFIRM:-0}"
FROM="build-input"
while [ $# -gt 0 ]; do
  case "$1" in
    --yes|-y)       CONFIRM=1; shift ;;
    --from)         FROM="$2"; shift 2 ;;
    --model)        MODEL="$2"; shift 2 ;;
    -h|--help)      sed -n '2,30p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done
case "$FROM" in build-input|inference|append) ;; *) echo "bad --from: $FROM" >&2; exit 2 ;; esac

# ----------------------------------------------------------------------------
# Logging: tee everything to a timestamped file for auditability
# ----------------------------------------------------------------------------
mkdir -p "${ADHOC_DIR}"
STAMP="$("$TRACTION_PY" -c 'import datetime; print(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))')"
LOG_FILE="${ADHOC_DIR}/patch_run_${STAMP}.log"
exec > >(tee -a "${LOG_FILE}") 2>&1

banner() { echo; echo "============================================================"; echo "  $*"; echo "============================================================"; }
step()   { echo "  [$(date '+%H:%M:%S')] $*"; }

rowcount() { # rowcount <csv> -> data rows (excl. header), or "MISSING"
  if [ -f "$1" ]; then "$TRACTION_PY" -c "import pandas as pd,sys; print(len(pd.read_csv(sys.argv[1],low_memory=False)))" "$1"; else echo "MISSING"; fi
}

banner "PATCH: general-agreement gap docs  |  log: ${LOG_FILE}"
step "traction python : ${TRACTION_PY}"
step "model           : ${MODEL} (prompt=${PROMPT_VARIANT})"
step "start phase     : ${FROM}   confirm-api=${CONFIRM}"
step "target file     : ${TARGET_CSV}  (rows now: $(rowcount "${TARGET_CSV}"))"

# phase ordering helper: should_run <phase> is true once we've reached FROM
_reached=0
should_run() { [ "$1" = "$FROM" ] && _reached=1; [ "$_reached" = "1" ]; }

# ----------------------------------------------------------------------------
# Phase 1 — build-input (no API)
# ----------------------------------------------------------------------------
if should_run "build-input"; then
  banner "PHASE 1/3 — build-input (assemble scoreable missing docs)"
  "$TRACTION_PY" "${PY_SCRIPT}" build-input
  step "input rows      : $(rowcount "${INPUT_CSV}")   -> ${INPUT_CSV}"
fi

# ----------------------------------------------------------------------------
# Phase 2 — inference via Batch API (HITS API; guarded by --yes)
# ----------------------------------------------------------------------------
if should_run "inference"; then
  banner "PHASE 2/3 — general-agreement inference (OpenAI Batch API)"
  if [ ! -f "${INPUT_CSV}" ]; then
    echo "ERROR: input CSV missing (${INPUT_CSV}); run phase build-input first." >&2; exit 1
  fi
  if [ "${CONFIRM}" != "1" ]; then
    step "SKIPPED — this step submits an OpenAI batch and costs money."
    step "Re-run with --yes (or CONFIRM=1) to execute it. Stopping here."
    banner "STOPPED before batch (prepare-only). Input ready: $(rowcount "${INPUT_CSV}") rows."
    exit 0
  fi
  step "submitting batch for $(rowcount "${INPUT_CSV}") rows ..."
  "$TRACTION_PY" "${INFER_SCRIPT}" \
    --data-file  "${INPUT_CSV}" \
    --output-dir "${ADHOC_DIR}" \
    --output-file "$(basename "${PATCH_CSV}")" \
    --model "${MODEL}" \
    --prompt-variant "${PROMPT_VARIANT}" \
    --submit --post-process \
    --max-output-tokens "${MAX_OUTPUT_TOKENS}"
  step "patch results   : $(rowcount "${PATCH_CSV}")   -> ${PATCH_CSV}"
fi

# ----------------------------------------------------------------------------
# Phase 3 — append (no API)
# ----------------------------------------------------------------------------
if should_run "append"; then
  banner "PHASE 3/3 — append patch into ${TARGET_CSV##*/}"
  if [ ! -f "${PATCH_CSV}" ]; then
    echo "ERROR: patch results missing (${PATCH_CSV}); run the inference phase first." >&2; exit 1
  fi
  before="$(rowcount "${TARGET_CSV}")"
  "$TRACTION_PY" "${PY_SCRIPT}" append
  after="$(rowcount "${TARGET_CSV}")"
  step "target rows     : ${before} -> ${after}"
fi

banner "DONE.  Full log: ${LOG_FILE}"
