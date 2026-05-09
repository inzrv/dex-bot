#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scenario_support import (  # noqa: E402
    ScenarioError,
    account_nonce,
    builder_request,
    contract_calldata,
    deployment_role,
    ensure_deployment,
    format_token_amount,
    print_step,
    public_transaction_payload,
    rpc,
    send_contract_transaction,
    start_block_builder,
    token_balance,
)

TOKEN_DECIMALS = 10**18
MINT_AMOUNT = 3 * TOKEN_DECIMALS
REAL_TRANSFER_AMOUNT = 1 * TOKEN_DECIMALS
SIMULATED_TRANSFER_AMOUNT = 1 * TOKEN_DECIMALS


def main() -> int:
    print_step("Preparing local chain")
    deployment = ensure_deployment()
    rpc_url = deployment["rpcUrl"]
    chain_id = int(deployment["chainId"])
    token_a = deployment["contracts"]["tokenA"]
    deployer_role = deployment_role(deployment, "deployer")
    victim_role = deployment_role(deployment, "victim")
    deployer = deployer_role["address"]
    victim = victim_role["address"]
    deployer_key = deployer_role["privateKey"]

    print(f"Deployer address: {deployer}")
    print(f"Victim address:   {victim}")

    print_step("Preparing local block builder")
    start_block_builder()

    print_step("Minting TokenA for transfer checks")
    rpc(rpc_url, "evm_setAutomine", [True])
    try:
        send_contract_transaction(
            rpc_url,
            deployer_key,
            token_a,
            "mint(address,uint256)",
            deployer,
            str(MINT_AMOUNT),
        )
    finally:
        rpc(rpc_url, "evm_setAutomine", [False])

    print_step("Mining a real transfer bundle")
    head_before_real = chain_head()
    real_payload = transfer_payload(
        rpc_url,
        chain_id,
        deployer,
        victim,
        token_a,
        REAL_TRANSFER_AMOUNT,
    )
    real_result = builder_request(
        "POST",
        "/private/bundle",
        {"transactions": [real_payload]},
    )
    real_tx_result = real_result["transactions"][0]
    head_after_real = chain_head()

    print(f"Head before real tx: {head_label(head_before_real)}")
    print(f"Head after real tx:  {head_label(head_after_real)}")
    print(f"Real bundle status:  {real_result['status']}")
    print(f"Real tx status:      {real_tx_result['status']}")

    if real_result["status"] != "included":
        raise ScenarioError(f"expected included real bundle, got {real_result['status']}")
    if real_tx_result["status"] != "included":
        raise ScenarioError(f"expected included real tx, got {real_tx_result['status']}")
    if block_number(head_after_real) <= block_number(head_before_real):
        raise ScenarioError("expected real bundle to advance the chain head")

    print_step("Simulating another transfer bundle")
    deployer_before_sim = token_balance(rpc_url, token_a, deployer)
    victim_before_sim = token_balance(rpc_url, token_a, victim)
    head_before_sim = chain_head()
    simulation_payload = transfer_payload(
        rpc_url,
        chain_id,
        deployer,
        victim,
        token_a,
        SIMULATED_TRANSFER_AMOUNT,
    )
    simulation_result = builder_request(
        "POST",
        "/private/bundle/simulate",
        {"transactions": [simulation_payload]},
    )
    simulation_tx_result = simulation_result["transactions"][0]
    head_after_sim = chain_head()
    deployer_after_sim = token_balance(rpc_url, token_a, deployer)
    victim_after_sim = token_balance(rpc_url, token_a, victim)

    print(f"Head before simulation: {head_label(head_before_sim)}")
    print(f"Head after simulation:  {head_label(head_after_sim)}")
    print(f"Simulation status:      {simulation_result['status']}")
    print(f"Simulation tx status:   {simulation_tx_result['status']}")
    print(f"Deployer TokenA before sim:    {format_token_amount(deployer_before_sim)}")
    print(f"Deployer TokenA after sim:     {format_token_amount(deployer_after_sim)}")
    print(f"Victim TokenA before sim:      {format_token_amount(victim_before_sim)}")
    print(f"Victim TokenA after sim:       {format_token_amount(victim_after_sim)}")

    if simulation_result["status"] != "included":
        raise ScenarioError(f"expected included simulation, got {simulation_result['status']}")
    if simulation_result.get("simulated") is not True:
        raise ScenarioError("expected simulation response to include simulated=true")
    if simulation_tx_result["status"] != "included":
        raise ScenarioError(f"expected included simulated tx, got {simulation_tx_result['status']}")
    if head_after_sim != head_before_sim:
        raise ScenarioError("chain head changed after bundle simulation")
    if deployer_after_sim != deployer_before_sim:
        raise ScenarioError("deployer TokenA balance changed after bundle simulation")
    if victim_after_sim != victim_before_sim:
        raise ScenarioError("victim TokenA balance changed after bundle simulation")

    print_step("Scenario complete")
    print("Bundle simulation returned receipts without changing block head or balances.")
    return 0


def transfer_payload(
    rpc_url: str,
    chain_id: int,
    sender: str,
    recipient: str,
    token: str,
    amount: int,
) -> dict[str, str]:
    calldata = contract_calldata(
        "transfer(address,uint256)",
        recipient,
        str(amount),
    )
    return public_transaction_payload(
        chain_id=chain_id,
        nonce=account_nonce(rpc_url, sender),
        sender=sender,
        to=token,
        calldata=calldata,
        gas=200_000,
    )


def chain_head() -> dict[str, Any]:
    return builder_request("GET", "/chain/head")


def block_number(head: dict[str, Any]) -> int:
    block_number_hex = head.get("blockNumber")
    if not isinstance(block_number_hex, str):
        raise ScenarioError("chain head response does not contain blockNumber")

    return int(block_number_hex, 16)


def head_label(head: dict[str, Any]) -> str:
    block_hash = head.get("blockHash")
    if not isinstance(block_hash, str):
        block_hash = "<missing>"

    return f"{block_number(head)} ({block_hash})"


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ScenarioError as error:
        print(f"\nScenario failed: {error}", file=sys.stderr)
        raise SystemExit(1)
