# Knight

Knight is the C++ arbitrage bot runtime for DEX Knight. It is intentionally small for now: it reads local config, starts a long-running idle loop, and waits for future mempool/core logic.

## Config

`config.json` stores local runtime settings.

```json
{
  "builderWsUrl": "ws://127.0.0.1:9001/ws/pending",
  "tlsVerifyPeer": true
}
```

`builderWsUrl` points to the Forest Gate pending transaction stream. Use `ws://` for the local block builder and `wss://` for TLS endpoints. `tlsVerifyPeer` is optional and defaults to `true`.

## Run With Local Scripts

From the repository root:

```shell
knight/bin/start-local.zsh
```

The script configures CMake, builds `knight`, starts it in the background, writes a PID file, writes a log file, and checks that the process did not exit immediately.

Runtime files:

```text
knight/runtime/knight.local.pid
knight/runtime/knight.local.log
```

Stop and clean the local bot runtime:

```shell
knight/bin/cleanup-local.zsh
```
