#!/usr/bin/env python3
from __future__ import annotations

import sys

from scenario_support import (
    BLOCKCHAIN_DIR,
    ENV_FILE,
    ScenarioError,
    builder_request,
    cast_int,
    ensure_deployment,
    print_step,
    read_env_file,
    rpc,
    run,
    start_block_builder,
    token_balance,
)

TRANSFER_AMOUNT = 10**18
MINT_AMOUNT = 100 * TRANSFER_AMOUNT


def main() -> int:
    env = read_env_file(ENV_FILE)

    print_step("Preparing local chain")
    deployment = ensure_deployment()
    rpc_url = deployment["rpcUrl"]
    chain_id = int(deployment["chainId"])
    token_a = deployment["contracts"]["tokenA"]
    deployer = deployment["deployer"]
    recipient = env["VICTIM_ADDRESS"]
    deployer_key = env["DEPLOYER_PRIVATE_KEY"]

    print_step("Preparing local block builder")
    start_block_builder()

    print_step("Minting TokenA for the sender")
    rpc(rpc_url, "evm_setAutomine", [True])
    try:
        run(
            [
                "cast",
                "send",
                token_a,
                "mint(address,uint256)",
                deployer,
                str(MINT_AMOUNT),
                "--private-key",
                deployer_key,
                "--rpc-url",
                rpc_url,
            ],
            cwd=BLOCKCHAIN_DIR,
        )
    finally:
        rpc(rpc_url, "evm_setAutomine", [False])

    sender_before = token_balance(rpc_url, token_a, deployer)
    recipient_before = token_balance(rpc_url, token_a, recipient)
    print(f"Sender TokenA before:    {sender_before}")
    print(f"Recipient TokenA before: {recipient_before}")

    print_step("Submitting transfer to the public mempool")
    nonce = cast_int(["cast", "nonce", deployer, "--rpc-url", rpc_url], cwd=BLOCKCHAIN_DIR)
    calldata = run(
        [
            "cast",
            "calldata",
            "transfer(address,uint256)",
            recipient,
            str(TRANSFER_AMOUNT),
        ],
        cwd=BLOCKCHAIN_DIR,
    ).stdout.strip()

    tx_payload = {
        "type": "0x2",
        "chainId": hex(chain_id),
        "nonce": hex(nonce),
        "from": deployer,
        "to": token_a,
        "value": "0x0",
        "gas": hex(200_000),
        "maxFeePerGas": hex(2_000_000_000),
        "maxPriorityFeePerGas": hex(1),
        "input": calldata,
    }
    mempool_record = builder_request("POST", "/public/tx", tx_payload)
    mempool_tx_id = mempool_record["mempoolTxId"]
    print(f"Mempool transaction: {mempool_tx_id}")
    print(f"Initial status:      {mempool_record['status']}")

    pending = builder_request("GET", "/public/pending")
    print(f"Pending transactions: {len(pending['transactions'])}")

    print_step("Mining the transfer through the private bundle endpoint")
    bundle_result = builder_request(
        "POST",
        "/private/bundle",
        {"transactions": [{"mempoolTxId": mempool_tx_id}]},
    )
    tx_result = bundle_result["transactions"][0]
    print(f"Bundle status:       {bundle_result['status']}")
    print(f"Chain transaction:   {tx_result['chainTxHash']}")
    print(f"Block number:        {int(tx_result['blockNumber'], 16)}")

    final_record = builder_request("GET", f"/public/tx/{mempool_tx_id}")
    sender_after = token_balance(rpc_url, token_a, deployer)
    recipient_after = token_balance(rpc_url, token_a, recipient)

    print_step("Checking final state")
    print(f"Final mempool status: {final_record['status']}")
    print(f"Sender TokenA after:  {sender_after}")
    print(f"Recipient after:      {recipient_after}")

    expected_recipient = recipient_before + TRANSFER_AMOUNT
    if bundle_result["status"] != "included":
        raise ScenarioError(f"expected included bundle, got {bundle_result['status']}")
    if final_record["status"] != "included":
        raise ScenarioError(f"expected included mempool record, got {final_record['status']}")
    if recipient_after != expected_recipient:
        raise ScenarioError(
            f"expected recipient balance {expected_recipient}, got {recipient_after}"
        )

    print_step("Scenario complete")
    print("Local chain and block builder are still running for inspection.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ScenarioError as error:
        print(f"\nScenario failed: {error}", file=sys.stderr)
        raise SystemExit(1)
