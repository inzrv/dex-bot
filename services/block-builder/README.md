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
POST /public/tx
GET /public/tx/{hash}
GET /public/pending
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

Submit a transaction to the in-memory mempool:

```shell
curl -X POST http://127.0.0.1:9001/public/tx \
  -H "Content-Type: application/json" \
  -d '{
    "hash": "0xabc",
    "type": "0x2",
    "chainId": "0x7a69",
    "nonce": "0x0",
    "from": "0x1111111111111111111111111111111111111111",
    "to": "0x2222222222222222222222222222222222222222",
    "value": "0x0",
    "gas": "0x493e0",
    "maxFeePerGas": "0x77359400",
    "maxPriorityFeePerGas": "0x1",
    "input": "0x"
  }'
```

The transaction is stored with status `pending`.

Read it back:

```shell
curl http://127.0.0.1:9001/public/tx/0xabc
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

## Planned Later

- `POST /public/tx` for victim transactions.
- `WS /public/pending` for the bot's pending transaction stream.
- `POST /private/bundle` for bot bundles.
- `GET /tx/{hash}` and `GET /bundle/{id}` for statuses.
- JSON-RPC calls from the builder to Anvil.
