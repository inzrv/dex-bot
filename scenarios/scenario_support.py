from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
SERVICE_DIR = REPO_ROOT / "services" / "block-builder"
BLOCKCHAIN_DIR = REPO_ROOT / "blockchain"
DEPLOYMENT_FILE = BLOCKCHAIN_DIR / "deployments" / "local.json"
ENV_FILE = BLOCKCHAIN_DIR / "config" / "local.anvil.env"

BUILDER_URL = os.environ.get("BLOCK_BUILDER_URL", "http://127.0.0.1:9001")


# Ensures a local blockchain deployment exists and returns its metadata.
def ensure_deployment() -> dict[str, Any]:
    if DEPLOYMENT_FILE.exists():
        deployment = read_json(DEPLOYMENT_FILE)
        if rpc_is_ready(deployment["rpcUrl"]):
            print(f"Using deployment: {DEPLOYMENT_FILE}")
            return deployment

        print("Saved deployment exists, but the local chain is not running.")

    run([str(BLOCKCHAIN_DIR / "bin" / "deploy-local.zsh")], cwd=REPO_ROOT)
    deployment = read_json(DEPLOYMENT_FILE)
    print(f"Using deployment: {DEPLOYMENT_FILE}")
    return deployment


# Starts the local block builder and waits until its health endpoint responds.
def start_block_builder() -> None:
    run([str(SERVICE_DIR / "bin" / "start-local.zsh")], cwd=REPO_ROOT)
    wait_for_builder()


# Waits for the block builder health endpoint to become available.
def wait_for_builder() -> None:
    for _ in range(30):
        try:
            builder_request("GET", "/health")
            return
        except ScenarioError:
            time.sleep(0.2)

    raise ScenarioError(f"block builder did not become healthy at {BUILDER_URL}/health")


# Reads an ERC-20 token balance from the local chain.
def token_balance(rpc_url: str, token: str, account: str) -> int:
    return cast_int(
        [
            "cast",
            "call",
            token,
            "balanceOf(address)(uint256)",
            account,
            "--rpc-url",
            rpc_url,
        ],
        cwd=BLOCKCHAIN_DIR,
    )


# Checks whether a JSON-RPC endpoint is reachable.
def rpc_is_ready(rpc_url: str) -> bool:
    try:
        rpc(rpc_url, "eth_blockNumber", [])
        return True
    except ScenarioError:
        return False


# Sends a JSON-RPC request and returns the result field.
def rpc(rpc_url: str, method: str, params: list[Any]) -> Any:
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
    ).encode("utf-8")
    request = Request(
        rpc_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError) as error:
        raise ScenarioError(f"RPC request failed: {error}") from error

    if "error" in result:
        raise ScenarioError(f"RPC error from {method}: {result['error']}")

    return result.get("result")


# Sends an HTTP request to the block builder API and returns the JSON response.
def builder_request(method: str, path: str, body: Optional[dict[str, Any]] = None) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(
        f"{BUILDER_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )

    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8")
        raise ScenarioError(f"builder {method} {path} failed: {detail}") from error
    except URLError as error:
        raise ScenarioError(f"builder {method} {path} failed: {error}") from error


# Runs a cast command and parses the first output token as an integer.
def cast_int(command: list[str], cwd: Path) -> int:
    output = run(command, cwd=cwd).stdout.strip()
    value = output.split()[0]
    return int(value, 0)


# Runs a subprocess and raises ScenarioError with useful command output.
def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as error:
        raise ScenarioError(f"required command not found: {command[0]}") from error
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or error.stdout.strip()
        raise ScenarioError(f"command failed: {' '.join(command)}\n{message}") from error


# Reads a JSON file into a dictionary.
def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


# Reads a simple KEY=VALUE env file into a dictionary.
def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    with path.open(encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"')
    return values


# Prints a visible step header for scenario output.
def print_step(message: str) -> None:
    print(f"\n==> {message}")


# Represents a scenario setup, execution, or validation failure.
class ScenarioError(RuntimeError):
    pass
