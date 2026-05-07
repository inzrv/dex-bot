// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20Backrun {
    function balanceOf(address account) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transfer(address to, uint256 amount) external returns (bool);
}

interface ISandboxDexBackrun {
    function tokenA() external view returns (address);
    function tokenB() external view returns (address);
    function swapExactAForB(uint256 amountIn, uint256 minAmountOut) external returns (uint256);
    function swapExactBForA(uint256 amountIn, uint256 minAmountOut) external returns (uint256);
}

contract SandboxBackrun {
    address public immutable operator;

    event BackrunExecuted(
        address indexed buyPool,
        address indexed sellPool,
        uint256 amountInB,
        uint256 amountOutA,
        uint256 amountOutB,
        uint256 profitB
    );
    event TokenWithdrawn(address indexed token, address indexed to, uint256 amount);

    modifier onlyOperator() {
        require(msg.sender == operator, "BACKRUN: operator");
        _;
    }

    constructor(address operator_) {
        require(operator_ != address(0), "BACKRUN: zero operator");
        operator = operator_;
    }

    function executeBackrun(
        address buyPool,
        address sellPool,
        uint256 amountInB,
        uint256 minAmountOutA,
        uint256 minAmountOutB,
        uint256 minProfitB
    ) external onlyOperator returns (uint256 amountOutA, uint256 amountOutB) {
        require(buyPool != address(0), "BACKRUN: zero buy pool");
        require(sellPool != address(0), "BACKRUN: zero sell pool");
        require(buyPool != sellPool, "BACKRUN: same pool");
        require(amountInB > 0, "BACKRUN: zero amount in");

        ISandboxDexBackrun buyDex = ISandboxDexBackrun(buyPool);
        ISandboxDexBackrun sellDex = ISandboxDexBackrun(sellPool);

        address tokenA = buyDex.tokenA();
        address tokenB = buyDex.tokenB();

        require(tokenA == sellDex.tokenA(), "BACKRUN: token A mismatch");
        require(tokenB == sellDex.tokenB(), "BACKRUN: token B mismatch");

        uint256 initialBalanceB = IERC20Backrun(tokenB).balanceOf(address(this));
        require(initialBalanceB >= amountInB, "BACKRUN: insufficient token B");

        _approve(tokenB, buyPool, amountInB);
        amountOutA = buyDex.swapExactBForA(amountInB, minAmountOutA);

        _approve(tokenA, sellPool, amountOutA);
        amountOutB = sellDex.swapExactAForB(amountOutA, minAmountOutB);

        uint256 finalBalanceB = IERC20Backrun(tokenB).balanceOf(address(this));
        uint256 profitB = finalBalanceB - initialBalanceB;
        require(profitB >= minProfitB, "BACKRUN: profit");

        emit BackrunExecuted(buyPool, sellPool, amountInB, amountOutA, amountOutB, profitB);
    }

    function withdrawToken(address token, address to, uint256 amount) external onlyOperator {
        require(token != address(0), "BACKRUN: zero token");
        require(to != address(0), "BACKRUN: zero to");
        require(IERC20Backrun(token).transfer(to, amount), "BACKRUN: transfer failed");

        emit TokenWithdrawn(token, to, amount);
    }

    function _approve(address token, address spender, uint256 amount) private {
        require(IERC20Backrun(token).approve(spender, amount), "BACKRUN: approve failed");
    }
}
