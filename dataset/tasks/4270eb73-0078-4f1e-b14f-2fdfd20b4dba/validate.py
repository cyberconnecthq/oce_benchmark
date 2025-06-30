from dataset.constants import (
    USDC_CONTRACT_ADDRESS_ETH,
    USDT_CONTRACT_ADDRESS_ETH,
    ERC20_ABI,
    AAVE_POOL_ADDRESS_ETH,
    AAVE_V3_POOL_ABI
)

from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount

RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"  # default anvil account
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

USDC = Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH)
USDT = Web3.to_checksum_address(USDT_CONTRACT_ADDRESS_ETH)
AAVE_POOL = Web3.to_checksum_address(AAVE_POOL_ADDRESS_ETH)

usdc_contract = w3.eth.contract(address=USDC, abi=ERC20_ABI)
usdt_contract = w3.eth.contract(address=USDT, abi=ERC20_ABI)
aave_pool = w3.eth.contract(address=AAVE_POOL, abi=AAVE_V3_POOL_ABI)

async def get_balances():
    eth_balance = w3.eth.get_balance(addr)
    usdc_balance = usdc_contract.functions.balanceOf(addr).call()
    usdt_balance = usdt_contract.functions.balanceOf(addr).call()

    # Query Aave V3 account data
    # getUserAccountData(address user) returns (totalCollateralBase, totalDebtBase, availableBorrowsBase, currentLiquidationThreshold, ltv, healthFactor)
    try:
        account_data = aave_pool.functions.getUserAccountData(addr).call()
        total_collateral = account_data[0] / 1e8  # unit: USD, 8 decimals
        total_debt = account_data[1] / 1e8
        available_borrow = account_data[2] / 1e8
        health_factor = account_data[5] / 1e18
    except Exception as e:
        total_collateral = total_debt = available_borrow = health_factor = None

    result = (
        f"Wallet Balances:\n"
        f"{eth_balance / 1e18:.6f} ETH\n"
        f"{usdc_balance / 1e6:.2f} USDC\n"
        f"{usdt_balance / 1e6:.2f} USDT\n\n"
    )
    if total_collateral is not None:
        result += (
            f"Aave V3 Info:\n"
            f"Total Collateral: {total_collateral:.2f} USD\n"
            f"Total Debt: {total_debt:.2f} USD\n"
            f"Available Borrow: {available_borrow:.2f} USD\n"
            f"Health Factor: {health_factor:.3f}\n"
        )
    else:
        result += "Failed to fetch Aave V3 info\n"
    return result

if __name__ == "__main__":
    import asyncio
    print(asyncio.run(get_balances()))
