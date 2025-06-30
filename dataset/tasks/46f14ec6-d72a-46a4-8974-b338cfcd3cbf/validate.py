from dataset.constants import PENDLE_MARKET_ADDRESS, PENDLE_PT_ADDRESS


from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import WETH_CONTRACT_ADDRESS_ETH, PENDLE_PT_ADDRESS

RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"  # 默认anvil账户
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

WETH = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH)
PT = Web3.to_checksum_address(PENDLE_PT_ADDRESS)

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
weth_contract = w3.eth.contract(address=WETH, abi=ERC20_ABI)
pt_contract = w3.eth.contract(address=PT, abi=ERC20_ABI)

async def get_balances():
    eth_balance = w3.eth.get_balance(addr)
    weth_balance = weth_contract.functions.balanceOf(addr).call()
    pt_balance = pt_contract.functions.balanceOf(addr).call()
    return (
        f"余额:\n"
        f"{eth_balance / 10**18} ETH\n"
        f"{weth_balance / 10**18} WETH\n"
        f"{pt_balance / 10**18} PT\n"
    )

if __name__ == '__main__':
    import asyncio
    print(asyncio.run(get_balances()))