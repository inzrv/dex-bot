#!/usr/bin/env zsh
set -euo pipefail

# Resolve paths relative to this script, so it can be called from any directory.
SCRIPT_DIR="${0:A:h}"
BLOCKCHAIN_DIR="${SCRIPT_DIR:h}"
ENV_FILE="${BLOCKCHAIN_DIR}/config/local.anvil.env"
DEPLOYMENTS_DIR="${BLOCKCHAIN_DIR}/deployments"
ADDRESSES_FILE="${DEPLOYMENTS_DIR}/local.json"
ANVIL_LOG="${DEPLOYMENTS_DIR}/anvil.local.log"
ANVIL_PID_FILE="${DEPLOYMENTS_DIR}/anvil.local.pid"

source "${ENV_FILE}"

ANVIL_PID=""

# Wait until Anvil accepts JSON-RPC requests.
wait_for_rpc() {
  for _ in {1..30}; do
    if cast block-number --rpc-url "${RPC_URL}" >/dev/null 2>&1; then
      return 0
    fi

    sleep 0.2
  done

  echo "RPC did not become ready at ${RPC_URL}" >&2
  return 1
}

# Deploy one contract and return only its deployed address on the last line.
deploy_contract() {
  local contract_id="$1"
  local label="$2"
  local output address

  echo "Deploying ${label}"
  output="$(
    forge create --broadcast "${contract_id}" \
      --rpc-url "${RPC_URL}" \
      --private-key "${DEPLOYER_PRIVATE_KEY}" \
      --constructor-args "${DEPLOYER_ADDRESS}"
  )"

  echo "${output}"
  address="$(echo "${output}" | awk '/Deployed to:/ { print $3; exit }')"

  if [[ -z "${address}" ]]; then
    echo "Could not read deployed address for ${label}" >&2
    return 1
  fi

  echo "${address}"
}

is_our_anvil_running() {
  if [[ ! -f "${ANVIL_PID_FILE}" ]]; then
    return 1
  fi

  local pid
  pid="$(cat "${ANVIL_PID_FILE}")"

  if ! kill -0 "${pid}" >/dev/null 2>&1; then
    return 1
  fi

  ps -p "${pid}" -o comm= | grep -q "anvil"
}

confirm_redeploy() {
  local reply

  echo "A local chain is already running at ${RPC_URL}."
  echo "Redeploying will create new TokenA/TokenB contracts and overwrite ${ADDRESSES_FILE}."
  printf "Continue? [y/N] "
  read -r reply

  case "${reply}" in
    y|Y|yes|YES)
      return 0
      ;;
    *)
      echo "Deployment cancelled"
      return 1
      ;;
  esac
}

mkdir -p "${DEPLOYMENTS_DIR}"
cd "${BLOCKCHAIN_DIR}"

# Reuse an already running local chain when possible. Otherwise start Anvil in
# the background and store its PID so cleanup-local.zsh can stop it later.
if cast block-number --rpc-url "${RPC_URL}" >/dev/null 2>&1; then
  if ! is_our_anvil_running; then
    echo "A chain is already running at ${RPC_URL}, but it was not started by this workflow." >&2
    echo "Refusing to deploy because cleanup-local.zsh would not know how to stop it safely." >&2
    echo "Stop that chain manually or change RPC_URL, then run this script again." >&2
    exit 1
  fi

  confirm_redeploy
  echo "Using existing local chain at ${RPC_URL}"
else
  echo "Starting local Anvil at ${RPC_URL}"
  anvil \
    --chain-id "${CHAIN_ID}" \
    --hardfork "${HARD_FORK}" \
    --block-base-fee-per-gas "${BASE_FEE_WEI}" \
    --gas-limit "${GAS_LIMIT}" \
    --mnemonic "${MNEMONIC}" \
    --accounts "${ACCOUNTS}" \
    --balance "${BALANCE_ETH}" \
    >"${ANVIL_LOG}" 2>&1 &

  ANVIL_PID="$!"
  echo "${ANVIL_PID}" >"${ANVIL_PID_FILE}"
  disown "${ANVIL_PID}" >/dev/null 2>&1 || true
  wait_for_rpc
  echo "Anvil started with PID ${ANVIL_PID}"
fi

# Make sure the chain is reachable before compiling and broadcasting deploys.
BLOCK_NUMBER="$(cast block-number --rpc-url "${RPC_URL}")"
echo "Local chain block number: ${BLOCK_NUMBER}"

echo "Compiling contracts"
forge build

# Deploy both sandbox tokens. The deployer is also the token minter for now.
TOKEN_A_ADDRESS="$(deploy_contract "src/tokens/TokenA.sol:TokenA" "TokenA" | tail -n 1)"
TOKEN_B_ADDRESS="$(deploy_contract "src/tokens/TokenB.sol:TokenB" "TokenB" | tail -n 1)"

# Read a simple on-chain value from each token to prove the deployments work.
TOKEN_A_SYMBOL="$(cast call "${TOKEN_A_ADDRESS}" "symbol()(string)" --rpc-url "${RPC_URL}")"
TOKEN_B_SYMBOL="$(cast call "${TOKEN_B_ADDRESS}" "symbol()(string)" --rpc-url "${RPC_URL}")"
TOKEN_A_SYMBOL="${TOKEN_A_SYMBOL#\"}"
TOKEN_A_SYMBOL="${TOKEN_A_SYMBOL%\"}"
TOKEN_B_SYMBOL="${TOKEN_B_SYMBOL#\"}"
TOKEN_B_SYMBOL="${TOKEN_B_SYMBOL%\"}"

# Leave the deployed sandbox in builder-controlled mining mode.
cast rpc evm_setAutomine false --rpc-url "${RPC_URL}" >/dev/null
AUTOMINE=false

# Save deployment output for the future C++ bot and for manual inspection.
cat >"${ADDRESSES_FILE}" <<EOF
{
  "chainId": ${CHAIN_ID},
  "rpcUrl": "${RPC_URL}",
  "hardFork": "${HARD_FORK}",
  "baseFeeWei": "${BASE_FEE_WEI}",
  "gasLimit": "${GAS_LIMIT}",
  "automine": ${AUTOMINE},
  "deployer": "${DEPLOYER_ADDRESS}",
  "contracts": {
    "tokenA": "${TOKEN_A_ADDRESS}",
    "tokenB": "${TOKEN_B_ADDRESS}"
  },
  "checks": {
    "tokenASymbol": "${TOKEN_A_SYMBOL}",
    "tokenBSymbol": "${TOKEN_B_SYMBOL}"
  }
}
EOF

echo "TokenA symbol: ${TOKEN_A_SYMBOL}"
echo "TokenA address: ${TOKEN_A_ADDRESS}"
echo "TokenB symbol: ${TOKEN_B_SYMBOL}"
echo "TokenB address: ${TOKEN_B_ADDRESS}"
echo "Hard fork: ${HARD_FORK}"
echo "Base fee wei: ${BASE_FEE_WEI}"
echo "Gas limit: ${GAS_LIMIT}"
echo "Automine: ${AUTOMINE}"
echo "Saved deployment addresses to ${ADDRESSES_FILE}"
