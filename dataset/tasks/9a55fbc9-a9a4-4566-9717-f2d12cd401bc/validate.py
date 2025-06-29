from dataset.constants import ACROSS_PROTOCOL_ADDRESS_ETH, WETH_CONTRACT_ADDRESS_ETH, ERC20_ABI

from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount

RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" #the first default anvil account
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

ACROSS = Web3.to_checksum_address(ACROSS_PROTOCOL_ADDRESS_ETH)
WETH = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH)


weth_contract = w3.eth.contract(address=WETH, abi=ERC20_ABI)


async def get_balances():
    eth_balance = w3.eth.get_balance(addr)
    weth_balance_across = weth_contract.functions.balanceOf(ACROSS).call()
    weth_balance = weth_contract.functions.balanceOf(addr).call()
    return (
        f"Balances:\n"
        f"{eth_balance / 10**18} ETH in wallet\n"
        f"{weth_balance / 10**18} WETH in wallet\n\n"
        f"Balance of Across:\n{weth_balance_across / 10**18} WETH\n"
    )


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(get_balances()))
