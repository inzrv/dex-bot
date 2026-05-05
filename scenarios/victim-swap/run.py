#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scenario_support import (  # noqa: E402
    ScenarioError,
    account_nonce,
    builder_request,
    contract_calldata,
    deployment_role,
    ensure_deployment,
    ensure_pool_liquidity,
    mint_and_approve,
    print_step,
    public_transaction_payload,
    quote_amount_out_a_for_b,
    start_block_builder,
    token_balance,
)

TOKEN_DECIMALS = 10**18
POOL_SEED_AMOUNT = 100_000 * TOKEN_DECIMALS
SWAP_AMOUNT_A = 100 * TOKEN_DECIMALS


def main() -> int:
    print_step("Preparing local chain")
    deployment = ensure_deployment()
    rpc_url = deployment["rpcUrl"]
    chain_id = int(deployment["chainId"])
    contracts = deployment["contracts"]
    token_a = contracts["tokenA"]
    token_b = contracts["tokenB"]
    pool = contracts["pool1"]
    deployer_role = deployment_role(deployment, "deployer")
    victim_role = deployment_role(deployment, "victim")
    deployer = deployer_role["address"]
    victim = victim_role["address"]

    print(f"Deployer address: {deployer}")
    print(f"Victim address:   {victim}")
    print(f"Pool address:     {pool}")

    print_step("Preparing local block builder")
    start_block_builder()

    ensure_pool_liquidity(
        rpc_url,
        deployer_role["privateKey"],
        deployer,
        token_a,
        token_b,
        pool,
        POOL_SEED_AMOUNT,
    )
    print_step("Preparing victim TokenA and approval")
    mint_and_approve(
        rpc_url,
        deployer_role["privateKey"],
        victim_role["privateKey"],
        victim,
        token_a,
        pool,
        SWAP_AMOUNT_A,
    )

    quoted_amount_out = quote_amount_out_a_for_b(rpc_url, pool, SWAP_AMOUNT_A)
    min_amount_out = quoted_amount_out * 99 // 100
    print(f"Quoted TokenB out:  {quoted_amount_out}")
    print(f"Minimum TokenB out: {min_amount_out}")

    victim_a_before = token_balance(rpc_url, token_a, victim)
    victim_b_before = token_balance(rpc_url, token_b, victim)

    print_step("Submitting victim swap to the public mempool")
    calldata = contract_calldata(
        "swapExactAForB(uint256,uint256)",
        str(SWAP_AMOUNT_A),
        str(min_amount_out),
    )
    mempool_record = builder_request(
        "POST",
        "/public/tx",
        public_transaction_payload(
            chain_id=chain_id,
            nonce=account_nonce(rpc_url, victim),
            sender=victim,
            to=pool,
            calldata=calldata,
        ),
    )
    mempool_tx_id = mempool_record["mempoolTxId"]
    print(f"Mempool transaction: {mempool_tx_id}")

    print_step("Mining the victim swap through the private bundle endpoint")
    bundle_result = builder_request(
        "POST",
        "/private/bundle",
        {"transactions": [{"mempoolTxId": mempool_tx_id}]},
    )
    tx_result = bundle_result["transactions"][0]
    print(f"Bundle status:     {bundle_result['status']}")
    print(f"Swap tx status:    {tx_result['status']}")
    print(f"Chain transaction: {tx_result['chainTxHash']}")

    final_record = builder_request("GET", f"/public/tx/{mempool_tx_id}")
    victim_a_after = token_balance(rpc_url, token_a, victim)
    victim_b_after = token_balance(rpc_url, token_b, victim)
    spent_a = victim_a_before - victim_a_after
    received_b = victim_b_after - victim_b_before

    print_step("Checking victim balances")
    print(f"Victim TokenA before: {victim_a_before}")
    print(f"Victim TokenA after:  {victim_a_after}")
    print(f"Victim TokenB before: {victim_b_before}")
    print(f"Victim TokenB after:  {victim_b_after}")
    print(f"Victim spent TokenA:  {spent_a}")
    print(f"Victim got TokenB:    {received_b}")

    if bundle_result["status"] != "included":
        raise ScenarioError(f"expected included bundle, got {bundle_result['status']}")
    if tx_result["status"] != "included":
        raise ScenarioError(f"expected included swap, got {tx_result['status']}")
    if final_record["status"] != "included":
        raise ScenarioError(f"expected included mempool record, got {final_record['status']}")
    if spent_a != SWAP_AMOUNT_A:
        raise ScenarioError(f"expected victim to spend {SWAP_AMOUNT_A} TokenA, got {spent_a}")
    if received_b < min_amount_out:
        raise ScenarioError(f"expected at least {min_amount_out} TokenB, got {received_b}")

    print_step("Scenario complete")
    print("Victim swap was mined and satisfied the minimum output.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ScenarioError as error:
        print(f"\nScenario failed: {error}", file=sys.stderr)
        raise SystemExit(1)
