



from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import (
    USDC_CONTRACT_ADDRESS_ETH,
    WETH_CONTRACT_ADDRESS_ETH,
    UNISWAP_V3_POOL_ADDRESS_WETH_USDC
)

RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" #the first default anvil account
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

USDC = Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH)
WETH = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH)
POOL = Web3.to_checksum_address(UNISWAP_V3_POOL_ADDRESS_WETH_USDC)

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

usdc_contract = w3.eth.contract(address=USDC, abi=ERC20_ABI)
weth_contract = w3.eth.contract(address=WETH, abi=ERC20_ABI)
pool_contract = w3.eth.contract(address=POOL, abi=ERC20_ABI)

async def get_balances():
    eth_balance = w3.eth.get_balance(addr)
    # 获取USDC余额
    usdc_balance = usdc_contract.functions.balanceOf(addr).call()
    # 获取WETH余额
    weth_balance = weth_contract.functions.balanceOf(addr).call()
    # 获取池子余额
    pool_weth_balance = weth_contract.functions.balanceOf(POOL).call()
    pool_usdc_balance = usdc_contract.functions.balanceOf(POOL).call()
    
    return (
        f"当前钱包余额:\n"
        f"{eth_balance / 10**18} ETH\n"
        f"{usdc_balance / 10**6} USDC\n"
        f"{weth_balance / 10**18} WETH\n"
        f"Pool WETH: {pool_weth_balance / 10**18} WETH\n"
        f"Pool USDC: {pool_usdc_balance / 10**6} USDC\n"
    )

if __name__ == '__main__':
    import asyncio
    print(asyncio.run(get_balances()))
