// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {SandboxDex} from "./SandboxDex.sol";

contract Pool2 is SandboxDex {
    constructor(address tokenA_, address tokenB_) SandboxDex(tokenA_, tokenB_) {}
}
