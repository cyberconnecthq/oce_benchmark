from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import WETH_CONTRACT_ADDRESS_ETH, AAVE_POOL_ADDRESS_ETH

RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"  # the first default anvil account
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address
SPENDER_A = Web3.to_checksum_address(AAVE_POOL_ADDRESS_ETH)
WETH = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH)

# ERC20 ABI with allowance function
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

# Get contract instance for WETH
weth_contract = w3.eth.contract(address=WETH, abi=ERC20_ABI)

async def get_balances():
    # Check allowance of addr for WETH contract to SPENDER_A
    allowance = weth_contract.functions.allowance(addr, SPENDER_A).call()
    return (
        f"WETH Allowance for address {SPENDER_A}:\n"
        f"{allowance / 10**18} WETH\n"
    )

if __name__ == "__main__":
    import asyncio
    print(asyncio.run(get_balances()))