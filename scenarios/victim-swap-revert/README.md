# Victim Swap Revert Scenario

This scenario checks that the pool reverts a victim swap whose `minAmountOut`
is impossible to satisfy.

It

- starts or reuses the local chain and block builder,
- ensures `Pool1` has liquidity, mints `100 TokenA` to the victim,
- approves `Pool1`, reads `getAmountOutAForB`,
- submits `swapExactAForB` with `minAmountOut = quote + 1` through the public mempool,
- mines it through the private bundle endpoint,
- verifies that the transaction is marked `reverted` and victim token balances do not change.

Run from the repository root:

```shell
scenarios/victim-swap-revert/run.zsh
```
