// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {SandboxERC20} from "./SandboxERC20.sol";

contract TokenA is SandboxERC20 {
    constructor(address minter) SandboxERC20("Sandbox Token A", "TKA", minter) {}
}
