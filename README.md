# DEX Bot

Local sandbox for building and testing a DEX bot workflow. The project is split into a local blockchain module, a block builder service, and root-level integration scenarios that exercise the pieces together.

## Modules

- `blockchain/`
  - local EVM network,
  - ERC-20,
  - AMM,
  - backrun executor,
  - Foundry deployment scripts.
- `services/block-builder/` - Python block builder service with public mempool and private bundle APIs.
- `scenarios/` - integration scenarios that coordinate the chain, builder, and future bot-facing flows.

## Stack

- Solidity contracts.
- Foundry: `anvil`, `forge`, `cast`.
- Python, FastAPI, Uvicorn.
- zsh local workflow scripts.

## Local Commands

### Blockchain

Start or redeploy the local blockchain sandbox:

```shell
blockchain/bin/deploy-local.zsh
```

Stop and clean the local blockchain sandbox:

```shell
blockchain/bin/cleanup-local.zsh
```

### Block Builder

Start the local block builder:

```shell
services/block-builder/bin/start-local.zsh
```

Stop and clean the local block builder:

```shell
services/block-builder/bin/cleanup-local.zsh
```

### Scenarios

Run the smoke scenario:

```shell
scenarios/token-transfer/run.zsh
```

The scenario starts or reuses the local chain and block builder, sends a `TokenA` transfer through the public mempool, mines it through a private bundle, and checks the final balance.

Seed both AMM pools:

```shell
scenarios/seed-pools/run.zsh
```

Run a successful victim swap through the public mempool:

```shell
scenarios/victim-swap/run.zsh
```

Run a victim swap that should revert on slippage:

```shell
scenarios/victim-swap-revert/run.zsh
```

Run a victim swap plus a simple backrun bundle:

```shell
scenarios/backrun/run.zsh
```

Check that bundle simulation returns receipts without changing chain state:

```shell
scenarios/bundle-simulation/run.zsh
```

## More Detail

- `blockchain/README.md` - local chain, contracts, deployment output, and
  Foundry usage.
- `services/block-builder/README.md` - builder setup, service runtime, and API
  examples.
