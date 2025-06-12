from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import USDT_CONTRACT_ADDRESS_ETH


RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" #the first default anvil account
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

USDT = Web3.to_checksum_address(USDT_CONTRACT_ADDRESS_ETH)

# ERC20 ABI
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

usdt_contract = w3.eth.contract(address=USDT, abi=ERC20_ABI)

# Aave V3 Pool ABI (简化版本,只包含借贷相关)
AAVE_POOL_ABI = [
    {
        "inputs": [{"name": "user", "type": "address"}],
        "name": "getUserAccountData",
        "outputs": [
            {"name": "totalCollateralBase", "type": "uint256"},
            {"name": "totalDebtBase", "type": "uint256"},
            {"name": "availableBorrowsBase", "type": "uint256"},
            {"name": "currentLiquidationThreshold", "type": "uint256"},
            {"name": "ltv", "type": "uint256"},
            {"name": "healthFactor", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

AAVE_POOL_ADDRESS = Web3.to_checksum_address("0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2")  # Aave V3 Pool地址
aave_pool = w3.eth.contract(address=AAVE_POOL_ADDRESS, abi=AAVE_POOL_ABI)

async def get_balances():
    # 获取USDT余额
    usdt_balance = usdt_contract.functions.balanceOf(addr).call()
    
    # 获取Aave借贷信息
    (total_collateral, total_debt, available_borrows, _, _, health_factor) = aave_pool.functions.getUserAccountData(addr).call()
    
    return (
        f"当前钱包余额:\n"
        f"{usdt_balance / 10**6} USDT\n\n"
        f"Aave借贷状态:\n"
        f"总抵押品: {total_collateral / 10**8} USD\n" 
        f"总债务: {total_debt / 10**8} USD\n"
        f"可借额度: {available_borrows / 10**8} USD\n"
        f"健康因子: {health_factor / 10**18}\n"
    )


if __name__ == '__main__':
    import asyncio
    print(asyncio.run(get_balances()))