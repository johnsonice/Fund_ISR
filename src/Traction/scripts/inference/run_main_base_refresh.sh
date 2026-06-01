#!/usr/bin/env bash
# Orchestrate a fresh main-pipeline base refresh:
#   1. Run the 4 fine-tuned per-task inference jobs (run_all.sh) AND
#      the zero-shot general-agreement job in parallel — they consume
#      different inputs (document_by_type_sector.csv vs df_documents.csv)
#      so there's no data dependency between them.
#   2. After both groups complete, build the final dataset
#      (df_fin.csv + df_fin_reg_core.csv).
#
# Once df_fin_reg_core.csv is validated, the user can repoint
# incremental_update/08_merge_all_incremental.py via --main-dir to merge
# incremental results against this fresh base.
set -euo pipefail

scripts_dir="$(cd "$(dirname "$0")" && pwd)"

echo "=== Stage 1: parallel inference (4 per-task jobs + general agreement) ==="
bash "$scripts_dir/run_all.sh" &
pid_all=$!

bash "$scripts_dir/run_general_agreement.sh" &
pid_general=$!

status=0
if ! wait "$pid_all"; then
  echo "run_all.sh failed" >&2
  status=$?
fi
if ! wait "$pid_general"; then
  echo "run_general_agreement.sh failed" >&2
  status=$?
fi

if [ "$status" -ne 0 ]; then
  echo "Stage 1 failed (status=$status); skipping final-dataset build." >&2
  exit "$status"
fi

echo "=== Stage 2: build final dataset ==="
bash "$scripts_dir/run_create_final_dataset.sh"

echo "Done. Outputs in ${MAIN_BASE_DIR:-/data/home/xiong/data/Fund/CSR/Tractions/output/main_base}/"
