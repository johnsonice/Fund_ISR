#!/usr/bin/env bash
# Run every other script in this folder in parallel and bubble up failures.
set -euo pipefail

scripts_dir="$(cd "$(dirname "$0")" && pwd)"
pids=()

# Kick off every sibling script (except this one) in the background.
for script in "$scripts_dir"/*.sh; do
  [ -e "$script" ] || continue

  script_base="$(basename "$script")"
  if [ "$script_base" = "run_all.sh" ] || [ "$script_base" = "run_post_process_all.sh" ]; then
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

