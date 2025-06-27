from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import SHIB_CONTRACT_ADDRESS_ETH, WETH_CONTRACT_ADDRESS_ETH, RPC_URL, PRIVATE_KEY

w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

WETH  = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH)
SHIB  = Web3.to_checksum_address(SHIB_CONTRACT_ADDRESS_ETH)

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
shib_contract = w3.eth.contract(address=SHIB, abi=ERC20_ABI)
weth_contract = w3.eth.contract(address=WETH, abi=ERC20_ABI)

async def get_balances():
    eth_balance= w3.eth.get_balance(addr)
    shib_balance = shib_contract.functions.balanceOf(addr).call()
    weth_balance= weth_contract.functions.balanceOf(addr).call()
    return (
        f"Balances:\n"
        f"{eth_balance / 10**18} ETH\n"
        f"{shib_balance / 10**18} SHIB\n"
        f"{weth_balance / 10**18} WETH\n"
    )

if __name__ == '__main__':
    import asyncio 
    print(asyncio.run(get_balances()))