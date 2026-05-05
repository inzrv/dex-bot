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

# Put Anvil into normal mining mode before deployment broadcasts. Previous
# scenarios leave automine disabled so the block builder can control mining.
prepare_for_deploy() {
  echo "Enabling automine for contract deployment"
  cast rpc evm_setAutomine true --rpc-url "${RPC_URL}" >/dev/null

  # Mine once to clear any pending transaction left by an interrupted redeploy.
  cast rpc evm_mine --rpc-url "${RPC_URL}" >/dev/null
}

# Deploy one contract and return only its deployed address on the last line.
deploy_contract() {
  local contract_id="$1"
  local label="$2"
  shift 2
  local output address

  echo "Deploying ${label}"
  output="$(
    forge create --broadcast "${contract_id}" \
      --rpc-url "${RPC_URL}" \
      --private-key "${DEPLOYER_PRIVATE_KEY}" \
      --constructor-args "$@"
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
  echo "Redeploying will create new TokenA/TokenB and Pool1/Pool2 contracts and overwrite ${ADDRESSES_FILE}."
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
prepare_for_deploy

echo "Compiling contracts"
forge build

# Deploy both sandbox tokens. The deployer is also the token minter for now.
TOKEN_A_ADDRESS="$(deploy_contract "src/tokens/TokenA.sol:TokenA" "TokenA" "${DEPLOYER_ADDRESS}" | tail -n 1)"
TOKEN_B_ADDRESS="$(deploy_contract "src/tokens/TokenB.sol:TokenB" "TokenB" "${DEPLOYER_ADDRESS}" | tail -n 1)"

# Deploy two independent AMM pools over the same token pair.
POOL_1_ADDRESS="$(deploy_contract "src/dexes/Pool1.sol:Pool1" "Pool1" "${TOKEN_A_ADDRESS}" "${TOKEN_B_ADDRESS}" | tail -n 1)"
POOL_2_ADDRESS="$(deploy_contract "src/dexes/Pool2.sol:Pool2" "Pool2" "${TOKEN_A_ADDRESS}" "${TOKEN_B_ADDRESS}" | tail -n 1)"

# Read simple on-chain values to prove the deployments work.
TOKEN_A_SYMBOL="$(cast call "${TOKEN_A_ADDRESS}" "symbol()(string)" --rpc-url "${RPC_URL}")"
TOKEN_B_SYMBOL="$(cast call "${TOKEN_B_ADDRESS}" "symbol()(string)" --rpc-url "${RPC_URL}")"
TOKEN_A_SYMBOL="${TOKEN_A_SYMBOL#\"}"
TOKEN_A_SYMBOL="${TOKEN_A_SYMBOL%\"}"
TOKEN_B_SYMBOL="${TOKEN_B_SYMBOL#\"}"
TOKEN_B_SYMBOL="${TOKEN_B_SYMBOL%\"}"

POOL_1_TOKEN_A="$(cast call "${POOL_1_ADDRESS}" "tokenA()(address)" --rpc-url "${RPC_URL}")"
POOL_1_TOKEN_B="$(cast call "${POOL_1_ADDRESS}" "tokenB()(address)" --rpc-url "${RPC_URL}")"
POOL_2_TOKEN_A="$(cast call "${POOL_2_ADDRESS}" "tokenA()(address)" --rpc-url "${RPC_URL}")"
POOL_2_TOKEN_B="$(cast call "${POOL_2_ADDRESS}" "tokenB()(address)" --rpc-url "${RPC_URL}")"
POOL_1_RESERVE_A="$(cast call "${POOL_1_ADDRESS}" "reserveA()(uint256)" --rpc-url "${RPC_URL}")"
POOL_1_RESERVE_B="$(cast call "${POOL_1_ADDRESS}" "reserveB()(uint256)" --rpc-url "${RPC_URL}")"
POOL_2_RESERVE_A="$(cast call "${POOL_2_ADDRESS}" "reserveA()(uint256)" --rpc-url "${RPC_URL}")"
POOL_2_RESERVE_B="$(cast call "${POOL_2_ADDRESS}" "reserveB()(uint256)" --rpc-url "${RPC_URL}")"

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
  "roles": {
    "deployer": {
      "address": "${DEPLOYER_ADDRESS}",
      "privateKey": "${DEPLOYER_PRIVATE_KEY}"
    },
    "victim": {
      "address": "${VICTIM_ADDRESS}",
      "privateKey": "${VICTIM_PRIVATE_KEY}"
    },
    "bot": {
      "address": "${BOT_ADDRESS}",
      "privateKey": "${BOT_PRIVATE_KEY}"
    },
    "treasury": {
      "address": "${TREASURY_ADDRESS}"
    }
  },
  "contracts": {
    "tokenA": "${TOKEN_A_ADDRESS}",
    "tokenB": "${TOKEN_B_ADDRESS}",
    "pool1": "${POOL_1_ADDRESS}",
    "pool2": "${POOL_2_ADDRESS}"
  },
  "checks": {
    "tokenASymbol": "${TOKEN_A_SYMBOL}",
    "tokenBSymbol": "${TOKEN_B_SYMBOL}",
    "pool1TokenA": "${POOL_1_TOKEN_A}",
    "pool1TokenB": "${POOL_1_TOKEN_B}",
    "pool1ReserveA": "${POOL_1_RESERVE_A}",
    "pool1ReserveB": "${POOL_1_RESERVE_B}",
    "pool2TokenA": "${POOL_2_TOKEN_A}",
    "pool2TokenB": "${POOL_2_TOKEN_B}",
    "pool2ReserveA": "${POOL_2_RESERVE_A}",
    "pool2ReserveB": "${POOL_2_RESERVE_B}"
  }
}
EOF

echo "TokenA symbol: ${TOKEN_A_SYMBOL}"
echo "TokenA address: ${TOKEN_A_ADDRESS}"
echo "TokenB symbol: ${TOKEN_B_SYMBOL}"
echo "TokenB address: ${TOKEN_B_ADDRESS}"
echo "Pool1 address: ${POOL_1_ADDRESS}"
echo "Pool1 tokenA: ${POOL_1_TOKEN_A}"
echo "Pool1 tokenB: ${POOL_1_TOKEN_B}"
echo "Pool1 reserveA: ${POOL_1_RESERVE_A}"
echo "Pool1 reserveB: ${POOL_1_RESERVE_B}"
echo "Pool2 address: ${POOL_2_ADDRESS}"
echo "Pool2 tokenA: ${POOL_2_TOKEN_A}"
echo "Pool2 tokenB: ${POOL_2_TOKEN_B}"
echo "Pool2 reserveA: ${POOL_2_RESERVE_A}"
echo "Pool2 reserveB: ${POOL_2_RESERVE_B}"
echo "Hard fork: ${HARD_FORK}"
echo "Base fee wei: ${BASE_FEE_WEI}"
echo "Gas limit: ${GAS_LIMIT}"
echo "Automine: ${AUTOMINE}"
echo "Saved deployment addresses to ${ADDRESSES_FILE}"
