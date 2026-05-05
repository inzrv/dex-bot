# Token Transfer Scenario

This scenario is a smoke test for the local blockchain and block builder.

It

- starts or reuses the local chain, 
- starts or reuses the block builder, 
- mints `100 TokenA` to the deployer,
- submits a `TokenA` transfer through the public mempool,
- mines it through the private bundle endpoint, 
- verifies the recipient balance.

Run from the repository root:

```shell
scenarios/token-transfer/run.zsh
```
