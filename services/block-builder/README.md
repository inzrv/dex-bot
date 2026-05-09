# Local Block Builder

This is the Python service skeleton for the future local block builder. The builder will eventually expose a public mempool API, a private bundle API, and an Anvil RPC integration.

## Install

From this directory:

```shell
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

If editable install fails because the virtual environment has an old `pip`, upgrade it and retry:

```shell
python -m pip install --upgrade pip
pip install -e .
```

## Run With Uvicorn

From this directory:

```shell
source .venv/bin/activate
uvicorn block_builder.app:create_app --factory --reload --host 127.0.0.1 --port 9001
```

## Run With Local Scripts

From the repository root:

```shell
services/block-builder/bin/start-local.zsh
```

The script creates `.venv` if needed, installs the package if needed, starts the service in the background, writes a PID file, writes a log file, and checks `/health`.

Runtime files:

```text
services/block-builder/runtime/block-builder.local.pid
services/block-builder/runtime/block-builder.local.log
```

Stop and clean the local service:

```shell
services/block-builder/bin/cleanup-local.zsh
```

## Run Via Entrypoint

After `pip install -e .`, this also works:

```shell
block-builder
```

This starts the same app without reload mode.

## Endpoints

```text
GET /health
GET /ping
GET /chain/head
POST /public/tx
GET /public/tx/{mempoolTxId}
GET /public/pending
POST /private/bundle
WS  /ws/pending
```

Example:

```shell
curl http://127.0.0.1:9001/ping
```

Expected response:

```json
{"message":"pong"}
```

Health check:

```shell
curl http://127.0.0.1:9001/health
```

Expected response:

```json
{"status":"ok"}
```

Read the current chain head through the builder:

```shell
curl http://127.0.0.1:9001/chain/head
```

Example response:

```json
{
  "blockNumber": "0x1",
  "blockHash": "0x...",
  "parentHash": "0x...",
  "timestamp": "0x...",
  "baseFeePerGas": "0x3b9aca00"
}
```

Submit a transaction to the in-memory mempool:

```shell
curl -X POST http://127.0.0.1:9001/public/tx \
  -H "Content-Type: application/json" \
  -d '{
    "type": "0x2",
    "chainId": "0x7a69",
    "nonce": "0x0",
    "from": "0xa0Ee7A142d267C1f36714E4a8F75612F20a79720",
    "to": "0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f",
    "value": "0x1",
    "gas": "0x493e0",
    "maxFeePerGas": "0x77359400",
    "maxPriorityFeePerGas": "0x1",
    "input": "0x"
  }'
```

The transaction is stored with status `pending`.
The response contains a generated `mempoolTxId`.

Read it back:

```shell
curl http://127.0.0.1:9001/public/tx/<mempoolTxId>
```

List pending transactions:

```shell
curl http://127.0.0.1:9001/public/pending
```

Open a WebSocket stream for pending transactions:

```shell
wscat -c ws://127.0.0.1:9001/ws/pending
```

Then submit a transaction from another terminal. The WebSocket client receives
one message for each new pending transaction.

Mine a block with a bundle. The bundle can contain one or more transactions.
For public mempool transactions, pass `mempoolTxId`; the builder resolves the
transaction from the mempool and updates its status after mining:

```shell
curl -X POST http://127.0.0.1:9001/private/bundle \
  -H "Content-Type: application/json" \
  -d '{
    "transactions": [
      {
        "mempoolTxId": "<mempoolTxId>"
      }
    ]
  }'
```

The bundle can also contain direct private transactions, which are not looked up
in the public mempool:

```json
{
  "transactions": [
    {
      "mempoolTxId": "mp-..."
    },
    {
      "type": "0x2",
      "chainId": "0x7a69",
      "nonce": "0x0",
      "from": "0x3c44cdddb6a900fa2b585dd299e03d12fa4293bc",
      "to": "0x...",
      "value": "0x0",
      "gas": "0x493e0",
      "maxFeePerGas": "0x77359400",
      "maxPriorityFeePerGas": "0x1",
      "input": "0x..."
    }
  ]
}
```

## Planned Later

- Bundle status storage.
- Configurable Anvil RPC URL instead of a hardcoded node address.
- Raw signed transactions and `eth_sendRawTransaction`.
