from dataset.constants import (
    BASE_RPC_URL,
    PRIVATE_KEY,
    WETH_CONTRACT_ADDRESS_BASE
)

from web3 import Web3, HTTPProvider

# USDC 合约地址（Base链）
USDC_CONTRACT_ADDRESS_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# ERC20 ABI（只需 balanceOf 和 decimals 方法）
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
        "stateMutability": "view"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
        "stateMutability": "view"
    }
]

async def get_balances():
    """
    获取Base链上当前账户的WETH和USDC余额
    """
    w3 = Web3(HTTPProvider(BASE_RPC_URL))
    account = w3.eth.account.from_key(PRIVATE_KEY)
    addr = account.address

    # 获取WETH余额
    weth = w3.eth.contract(address=Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_BASE), abi=ERC20_ABI)
    weth_decimals = weth.functions.decimals().call()
    weth_balance = weth.functions.balanceOf(addr).call() / (10 ** weth_decimals)

    # 获取USDC余额
    usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_BASE), abi=ERC20_ABI)
    usdc_decimals = usdc.functions.decimals().call()
    usdc_balance = usdc.functions.balanceOf(addr).call() / (10 ** usdc_decimals)

    print(f"WETH余额: {weth_balance}")
    print(f"USDC余额: {usdc_balance}")
    return {"weth": weth_balance, "usdc": usdc_balance}

if __name__=='__main__':
    import asyncio
    asyncio.run(get_balances())
