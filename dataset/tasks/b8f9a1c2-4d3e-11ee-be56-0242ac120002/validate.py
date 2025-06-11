from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount



RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" #the first default anvil account
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

WETH  = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0E5C4F27eAD9083C756Cc2")
PEPE  = Web3.to_checksum_address("0x6982508145454Ce325dDbE47a25d4ec3d2311933")

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
pepe_contract = w3.eth.contract(address=PEPE, abi=ERC20_ABI)
weth_contract = w3.eth.contract(address=WETH, abi=ERC20_ABI)



async def get_balances():
    eth_balance= w3.eth.get_balance(addr)
    pepe_balance = pepe_contract.functions.balanceOf(addr).call()
    weth_balance= weth_contract.functions.balanceOf(addr).call()
    return (
        f"Balances:\n"
        f"{eth_balance / 10**18} ETH\n"
        f"{pepe_balance / 10**6} PEPE\n"
        f"{weth_balance / 10**18} WETH\n"
    )


if __name__ == '__main__':
    import asyncio 
    print(asyncio.run(get_balances()))