from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import PEPE_CONTRACT_ADDRESS_ETH, RPC_URL, PRIVATE_KEY

w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address
SPENDER_A = Web3.to_checksum_address("0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
PEPE = Web3.to_checksum_address(PEPE_CONTRACT_ADDRESS_ETH)

# ERC20 ABI with only allowance function
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

# Get PEPE contract instance
pepe_contract = w3.eth.contract(address=PEPE, abi=ERC20_ABI)

async def get_balances():
    # Query PEPE allowance from addr to SPENDER_A
    allowance = pepe_contract.functions.allowance(addr, SPENDER_A).call()
    return (
        f"PEPE allowance of address {addr} to {SPENDER_A}:\n"
        f"{allowance} PEPE (raw value, not scaled)\n"
    )

if __name__ == "__main__":
    import asyncio
    print(asyncio.run(get_balances()))