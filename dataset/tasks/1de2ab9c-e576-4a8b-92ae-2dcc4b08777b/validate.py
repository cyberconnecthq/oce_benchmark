from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import WETH_CONTRACT_ADDRESS_ETH, USDC_CONTRACT_ADDRESS_ETH


RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" #the first default anvil account
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

WETH  = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH)
USDC  = Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH)
ROUTER= Web3.to_checksum_address("0xE592427A0AEce92De3Edee1F18E0157C05861564")
QUOTER= Web3.to_checksum_address("0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6")

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
usdc_contract = w3.eth.contract(address=USDC, abi=ERC20_ABI)
weth_contract = w3.eth.contract(address=WETH, abi=ERC20_ABI)



async def get_balances():
    eth_balance_before = w3.eth.get_balance(addr)
    usdc_balance_before = usdc_contract.functions.balanceOf(addr).call()
    weth_balance_before = weth_contract.functions.balanceOf(addr).call()
    return (
        f"Balances:\n"
        f"{eth_balance_before / 10**18} ETH\n"
        f"{usdc_balance_before / 10**6} USDC\n"
        f"{weth_balance_before / 10**18} WETH\n"
    )



if __name__ == "__main__":
    import asyncio
    print(asyncio.run(get_balances()))