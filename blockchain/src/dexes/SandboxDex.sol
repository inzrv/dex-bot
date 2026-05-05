// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20Like {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

contract SandboxDex {
    uint256 public constant FEE_NUMERATOR = 997;
    uint256 public constant FEE_DENOMINATOR = 1000;

    address public immutable tokenA;
    address public immutable tokenB;

    uint256 public reserveA;
    uint256 public reserveB;

    event LiquidityAdded(address indexed provider, uint256 amountA, uint256 amountB);
    event Swap(
        address indexed trader,
        address indexed tokenIn,
        address indexed tokenOut,
        uint256 amountIn,
        uint256 amountOut
    );

    constructor(address tokenA_, address tokenB_) {
        require(tokenA_ != address(0), "DEX: zero token A");
        require(tokenB_ != address(0), "DEX: zero token B");
        require(tokenA_ != tokenB_, "DEX: same token");

        tokenA = tokenA_;
        tokenB = tokenB_;
    }

    function seedLiquidity(uint256 amountA, uint256 amountB) external {
        require(amountA > 0, "DEX: zero amount A");
        require(amountB > 0, "DEX: zero amount B");

        _transferFrom(tokenA, msg.sender, address(this), amountA);
        _transferFrom(tokenB, msg.sender, address(this), amountB);

        reserveA += amountA;
        reserveB += amountB;

        emit LiquidityAdded(msg.sender, amountA, amountB);
    }

    function swapExactAForB(uint256 amountIn, uint256 minAmountOut) external returns (uint256 amountOut) {
        amountOut = _swapExactIn(
            tokenA,
            tokenB,
            amountIn,
            minAmountOut,
            reserveA,
            reserveB
        );

        reserveA += amountIn;
        reserveB -= amountOut;
    }

    function swapExactBForA(uint256 amountIn, uint256 minAmountOut) external returns (uint256 amountOut) {
        amountOut = _swapExactIn(
            tokenB,
            tokenA,
            amountIn,
            minAmountOut,
            reserveB,
            reserveA
        );

        reserveB += amountIn;
        reserveA -= amountOut;
    }

    function getAmountOut(
        uint256 amountIn,
        uint256 reserveIn,
        uint256 reserveOut
    ) public pure returns (uint256) {
        require(amountIn > 0, "DEX: zero amount in");
        require(reserveIn > 0, "DEX: empty reserve in");
        require(reserveOut > 0, "DEX: empty reserve out");

        uint256 amountInWithFee = amountIn * FEE_NUMERATOR;
        return (amountInWithFee * reserveOut) / ((reserveIn * FEE_DENOMINATOR) + amountInWithFee);
    }

    function getAmountOutAForB(uint256 amountIn) external view returns (uint256) {
        return getAmountOut(amountIn, reserveA, reserveB);
    }

    function getAmountOutBForA(uint256 amountIn) external view returns (uint256) {
        return getAmountOut(amountIn, reserveB, reserveA);
    }

    function getReserves() external view returns (uint256, uint256) {
        return (reserveA, reserveB);
    }

    function _swapExactIn(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 minAmountOut,
        uint256 reserveIn,
        uint256 reserveOut
    ) private returns (uint256 amountOut) {
        amountOut = getAmountOut(amountIn, reserveIn, reserveOut);
        require(amountOut > 0, "DEX: zero amount out");
        require(amountOut >= minAmountOut, "DEX: slippage");

        _transferFrom(tokenIn, msg.sender, address(this), amountIn);
        _transfer(tokenOut, msg.sender, amountOut);

        emit Swap(msg.sender, tokenIn, tokenOut, amountIn, amountOut);
    }

    function _transfer(address token, address to, uint256 amount) private {
        require(IERC20Like(token).transfer(to, amount), "DEX: transfer failed");
    }

    function _transferFrom(address token, address from, address to, uint256 amount) private {
        require(IERC20Like(token).transferFrom(from, to, amount), "DEX: transferFrom failed");
    }
}
