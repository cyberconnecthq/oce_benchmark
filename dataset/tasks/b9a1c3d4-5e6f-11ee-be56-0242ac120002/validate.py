from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount



RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" #the first default anvil account
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address
receiver_addr = Web3.to_checksum_address("0xAd4C0379544aE7efd56F2B58c7ffcfD63A1cb216")



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


async def get_balances():
    eth_balance= w3.eth.get_balance(addr)
    receiver_eth_balance = w3.eth.get_balance(receiver_addr)
    return (
        f"Balances of origin address:\n"
        f"{eth_balance / 10**18} ETH\n\n"
        f"Balance of address:{receiver_addr}:\n"
        f"{receiver_eth_balance / 10**18} ETH"
    )


if __name__ == '__main__':
    import asyncio 
    print(asyncio.run(get_balances()))