from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import USDT_CONTRACT_ADDRESS_ETH, WETH_CONTRACT_ADDRESS_ETH
from evaluate_utils.aave_v3_util import get_aave_info


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
weth_contract = w3.eth.contract(address=Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH), abi=ERC20_ABI)


async def get_balances():
    # 获取USDT余额
    usdt_balance = usdt_contract.functions.balanceOf(addr).call()
    
    aave_info = await get_aave_info(addr)
    
    return (
        f"Current wallet balance:\n"
        f"{usdt_balance / 10**6} USDT\n\n"
        f"{aave_info}"
    )


if __name__ == '__main__':
    import asyncio
    print(asyncio.run(get_balances()))