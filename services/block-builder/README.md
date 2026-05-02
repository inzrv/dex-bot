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

## Planned Later

- `POST /public/tx` for victim transactions.
- `WS /public/pending` for the bot's pending transaction stream.
- `POST /private/bundle` for bot bundles.
- `GET /tx/{hash}` and `GET /bundle/{id}` for statuses.
- JSON-RPC calls from the builder to Anvil.
