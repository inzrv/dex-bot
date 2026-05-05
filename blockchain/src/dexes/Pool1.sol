// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {SandboxDex} from "./SandboxDex.sol";

contract Pool1 is SandboxDex {
    constructor(address tokenA_, address tokenB_) SandboxDex(tokenA_, tokenB_) {}
}
