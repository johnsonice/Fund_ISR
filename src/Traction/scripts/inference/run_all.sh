#!/usr/bin/env bash
# Run the 4 per-task fine-tuned inference jobs in parallel and bubble up failures.
# Excludes general-agreement and final-dataset scripts — those have different
# inputs/dependencies and are sequenced separately by run_main_base_refresh.sh.
set -euo pipefail

scripts_dir="$(cd "$(dirname "$0")" && pwd)"
pids=()

# Exclude orchestration, general-agreement, final-dataset, and post-processing
# scripts — only the 4 per-task `run_{domain}_{task}.sh` scripts run here.
EXCLUDE_REGEX='^(run_all|run_main_base_refresh|run_general_agreement|run_create_final_dataset|run_post_process_all)\.sh$'

for script in "$scripts_dir"/*.sh; do
  [ -e "$script" ] || continue

  script_base="$(basename "$script")"
  if [[ "$script_base" =~ $EXCLUDE_REGEX ]]; then
    continue
  fi

  echo "Starting $(basename "$script")..."
  bash "$script" &
  pids+=("$!")
done

# Wait for all backgrounded scripts and surface any failure.
status=0
for pid in "${pids[@]}"; do
  if ! wait "$pid"; then
    status=$?
  fi
done

exit "$status"

