# Knight

Knight is the C++ arbitrage bot runtime for DEX Knight. It is intentionally small for now: it reads local config, starts a long-running idle loop, and waits for future mempool/core logic.

## Config

`config.json` stores local runtime settings.

```json
{
  "builderEndpoint": "http://127.0.0.1:9001"
}
```

`builderEndpoint` points to the local Forest Gate block builder API.

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
