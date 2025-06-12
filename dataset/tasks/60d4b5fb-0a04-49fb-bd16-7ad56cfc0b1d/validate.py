from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import LIDO_CONTRACT_ADDRESS_ETH


RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" #the first default anvil account
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

LIDO  = Web3.to_checksum_address(LIDO_CONTRACT_ADDRESS_ETH)
STETH = Web3.to_checksum_address(LIDO_CONTRACT_ADDRESS_ETH)

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

# 获取合约实例
lido_contract = w3.eth.contract(address=LIDO, abi=ERC20_ABI)


async def get_balances():
    eth_balance = w3.eth.get_balance(addr)
    lido_eth_balance = w3.eth.get_balance(LIDO)
    lido_balance = lido_contract.functions.balanceOf(addr).call()
    return (
        f"Balances:\n"
        f"{eth_balance / 10**18} ETH\n"
        f"{lido_balance / 10**18}  stETH\n\n"
        f"Balance of Lido contract:\n"
        f"{lido_eth_balance / 10**18}ETH\n"
    )

if __name__ == '__main__':
    import asyncio 
    print(asyncio.run(get_balances()))