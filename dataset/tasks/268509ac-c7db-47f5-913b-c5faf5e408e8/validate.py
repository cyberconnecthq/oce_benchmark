from web3 import Web3, HTTPProvider

from dataset.constants import WETH_CONTRACT_ADDRESS_ETH, BNB_CONTRACT_ADDRESS_ETH

# Ethereum RPC URL (local or public node)
ETH_RPC_URL = "http://127.0.0.1:8545"

# Default private key (for local testing only)
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

# ERC20 ABI (only balanceOf method)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

# Initialize web3 object
w3 = Web3(HTTPProvider(ETH_RPC_URL))

# Get account address
account = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

# Contract instances
weth_contract = w3.eth.contract(address=Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH), abi=ERC20_ABI)
bnb_contract = w3.eth.contract(address=Web3.to_checksum_address(BNB_CONTRACT_ADDRESS_ETH), abi=ERC20_ABI)

async def get_balances():
    # ETH balance
    eth_balance = w3.eth.get_balance(addr)
    # WETH balance
    weth_balance = weth_contract.functions.balanceOf(addr).call()
    # BNB balance
    bnb_balance = bnb_contract.functions.balanceOf(addr).call()
    return (
        f"Ethereum Mainnet:\n"
        f"ETH Balance: {eth_balance / 10**18} ETH\n"
        f"WETH Balance: {weth_balance / 10**18} WETH\n"
        f"BNB Balance: {bnb_balance / 10**18} BNB\n"
    )

if __name__ == '__main__':
    import asyncio
    print(asyncio.run(get_balances()))
