#!/usr/bin/env zsh
set -euo pipefail

# Resolve paths relative to this script, so it can be called from any directory.
SCRIPT_DIR="${0:A:h}"
BLOCKCHAIN_DIR="${SCRIPT_DIR:h}"
DEPLOYMENTS_DIR="${BLOCKCHAIN_DIR}/deployments"
ADDRESSES_FILE="${DEPLOYMENTS_DIR}/local.json"
ANVIL_LOG="${DEPLOYMENTS_DIR}/anvil.local.log"
ANVIL_PID_FILE="${DEPLOYMENTS_DIR}/anvil.local.pid"

stop_anvil() {
  local pid="$1"

  if ! kill -0 "${pid}" >/dev/null 2>&1; then
    echo "No running process found for saved Anvil PID ${pid}"
    return 0
  fi

  # Avoid killing an unrelated process if the PID file is stale.
  if ! ps -p "${pid}" -o comm= | grep -q "anvil"; then
    echo "Saved PID ${pid} is not an Anvil process; leaving it untouched"
    return 0
  fi

  echo "Stopping Anvil process ${pid}"
  kill "${pid}"

  for _ in {1..20}; do
    if ! kill -0 "${pid}" >/dev/null 2>&1; then
      return 0
    fi

    sleep 0.2
  done

  echo "Anvil process ${pid} did not exit after SIGTERM; sending SIGKILL"
  kill -9 "${pid}" >/dev/null 2>&1 || true
}

# Stop only the Anvil process started by deploy-local.zsh.
if [[ -f "${ANVIL_PID_FILE}" ]]; then
  ANVIL_PID="$(cat "${ANVIL_PID_FILE}")"
  stop_anvil "${ANVIL_PID}"
else
  echo "No local Anvil PID file found"
fi

# Remove runtime files produced by the local deployment workflow.
rm -f "${ANVIL_PID_FILE}"
rm -f "${ANVIL_LOG}"
rm -f "${ADDRESSES_FILE}"

echo "Local blockchain environment cleaned up"
