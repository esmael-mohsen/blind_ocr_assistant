#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

child_pid=""

stop_child() {
  if [[ -n "$child_pid" ]] && kill -0 "$child_pid" 2>/dev/null; then
    kill -TERM "$child_pid" 2>/dev/null || true
    wait "$child_pid" 2>/dev/null || true
  fi
}

trap stop_child INT TERM

python main.py "$@" &
child_pid="$!"
wait "$child_pid"
