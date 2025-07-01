from evaluate_utils.aave_v3_util import get_aave_info

from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import USDC_CONTRACT_ADDRESS_ETH
from evaluate_utils.aave_v3_util import get_aave_info

RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"  # 默认anvil账户
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

# ERC20 ABI for balanceOf
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

# USDC合约实例
usdc_contract = w3.eth.contract(address=Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH), abi=ERC20_ABI)

async def get_balances():
    # 获取ETH余额
    eth_balance = w3.eth.get_balance(addr)
    # 获取USDC余额
    usdc_balance = usdc_contract.functions.balanceOf(addr).call()
    # 获取Aave账户信息
    aave_info = await get_aave_info(addr)
    return (
        f"当前钱包余额:\n"
        f"{eth_balance / 10**18} ETH\n"
        f"{usdc_balance / 10**6} USDC\n\n"
        f"{aave_info}"
    )

if __name__ == '__main__':
    import asyncio
    print(asyncio.run(get_balances()))
