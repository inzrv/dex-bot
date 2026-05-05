#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scenario_support import (  # noqa: E402
    BLOCKCHAIN_DIR,
    ENV_FILE,
    ScenarioError,
    cast_int,
    ensure_deployment,
    print_step,
    read_env_file,
    rpc,
    run,
)

TOKEN_DECIMALS = 10**18
POOL_TOKEN_AMOUNT = 100_000 * TOKEN_DECIMALS


def main() -> int:
    env = read_env_file(ENV_FILE)

    print_step("Preparing local chain")
    deployment = ensure_deployment()
    rpc_url = deployment["rpcUrl"]
    contracts = deployment["contracts"]
    token_a = contracts["tokenA"]
    token_b = contracts["tokenB"]
    pool1 = contracts["pool1"]
    pool2 = contracts["pool2"]
    deployer_key = env["DEPLOYER_PRIVATE_KEY"]

    pools = [
        ("Pool1", pool1),
        ("Pool2", pool2),
    ]

    reserves_before = {
        label: pool_reserves(rpc_url, pool)
        for label, pool in pools
    }

    print_step("Minting pool seed tokens to the deployer")
    rpc(rpc_url, "evm_setAutomine", [True])
    try:
        total_amount = POOL_TOKEN_AMOUNT * len(pools)
        send(
            rpc_url,
            deployer_key,
            token_a,
            "mint(address,uint256)",
            deployment["deployer"],
            str(total_amount),
        )
        send(
            rpc_url,
            deployer_key,
            token_b,
            "mint(address,uint256)",
            deployment["deployer"],
            str(total_amount),
        )

        print_step("Approving pools")
        for label, pool in pools:
            send(rpc_url, deployer_key, token_a, "approve(address,uint256)", pool, str(POOL_TOKEN_AMOUNT))
            send(rpc_url, deployer_key, token_b, "approve(address,uint256)", pool, str(POOL_TOKEN_AMOUNT))
            print(f"{label} approved for {format_token_amount(POOL_TOKEN_AMOUNT)} TokenA and TokenB")

        print_step("Seeding pool liquidity")
        for label, pool in pools:
            send(
                rpc_url,
                deployer_key,
                pool,
                "seedLiquidity(uint256,uint256)",
                str(POOL_TOKEN_AMOUNT),
                str(POOL_TOKEN_AMOUNT),
            )
            print(f"{label} seeded")
    finally:
        rpc(rpc_url, "evm_setAutomine", [False])

    print_step("Checking reserves")
    for label, pool in pools:
        before_a, before_b = reserves_before[label]
        after_a, after_b = pool_reserves(rpc_url, pool)
        expected_a = before_a + POOL_TOKEN_AMOUNT
        expected_b = before_b + POOL_TOKEN_AMOUNT

        print(f"{label} reserveA before: {before_a}")
        print(f"{label} reserveB before: {before_b}")
        print(f"{label} reserveA after:  {after_a}")
        print(f"{label} reserveB after:  {after_b}")

        if after_a != expected_a:
            raise ScenarioError(f"{label} reserveA expected {expected_a}, got {after_a}")
        if after_b != expected_b:
            raise ScenarioError(f"{label} reserveB expected {expected_b}, got {after_b}")

    print_step("Scenario complete")
    print("Both pools received 100,000 TokenA and 100,000 TokenB.")
    return 0


def send(
    rpc_url: str,
    private_key: str,
    contract: str,
    signature: str,
    *args: str,
) -> None:
    run(
        [
            "cast",
            "send",
            contract,
            signature,
            *args,
            "--private-key",
            private_key,
            "--rpc-url",
            rpc_url,
        ],
        cwd=BLOCKCHAIN_DIR,
    )


def pool_reserves(rpc_url: str, pool: str) -> tuple[int, int]:
    reserve_a = cast_int(
        ["cast", "call", pool, "reserveA()(uint256)", "--rpc-url", rpc_url],
        cwd=BLOCKCHAIN_DIR,
    )
    reserve_b = cast_int(
        ["cast", "call", pool, "reserveB()(uint256)", "--rpc-url", rpc_url],
        cwd=BLOCKCHAIN_DIR,
    )
    return reserve_a, reserve_b


def format_token_amount(amount: int) -> str:
    return str(amount // TOKEN_DECIMALS)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ScenarioError as error:
        print(f"\nScenario failed: {error}", file=sys.stderr)
        raise SystemExit(1)
