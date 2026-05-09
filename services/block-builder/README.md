# Forest Gate

Forest Gate is the local block builder for DEX Knight. It keeps an in-memory
public mempool, accepts private bundles, talks to Anvil, and exposes small chain
gateway endpoints for the future bot.

Detailed endpoint examples live in [`docs/endpoints.md`](docs/endpoints.md).

## Run With Local Scripts

From the repository root:

```shell
services/block-builder/bin/start-local.zsh
```

The script creates `.venv` if needed, installs Python dependencies if needed, starts the
service from the local source tree in the background, writes a PID file, writes
a log file, and checks `/health`.

Runtime files:

```text
services/block-builder/runtime/block-builder.local.pid
services/block-builder/runtime/block-builder.local.log
```

Stop and clean the local service:

```shell
services/block-builder/bin/cleanup-local.zsh
```

## Planned Later

- Bundle status storage.
- Configurable Anvil RPC URL instead of a hardcoded node address.
- Raw signed transactions and `eth_sendRawTransaction`.
