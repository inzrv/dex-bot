# Seed Pools Scenario

This scenario prepares both deployed AMM pools with equal `TokenA` / `TokenB`
liquidity.

It

- starts or reuses the local chain,
- mints enough `TokenA` and `TokenB` to the deployer,
- approves `Pool1` and `Pool2`, adds `100,000` of each token to each pool,
- verifies the reserve changes.

Run from the repository root:

```shell
scenarios/seed-pools/run.zsh
```
