# Bundle Simulation Scenario

This scenario checks that bundle simulation produces execution results without
changing the real chain state.

It

- starts or reuses the local chain and block builder,
- mints `3 TokenA` to the deployer,
- mines one real `TokenA` transfer through `POST /private/bundle`,
- records the chain head after the real transfer,
- simulates another transfer through `POST /private/bundle/simulate`,
- verifies the block head and token balances did not change after simulation.

Run from the repository root:

```shell
scenarios/bundle-simulation/run.zsh
```
