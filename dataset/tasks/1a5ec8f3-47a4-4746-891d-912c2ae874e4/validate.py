from dataset.constants import ACROSS_PROTOCOL_ADDRESS_ETH, USDC_CONTRACT_ADDRESS_ETH, ERC20_ABI

from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount

RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" #the first default anvil account
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

ACROSS = Web3.to_checksum_address(ACROSS_PROTOCOL_ADDRESS_ETH)
USDC = Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH)


usdc_contract = w3.eth.contract(address=USDC, abi=ERC20_ABI)


async def get_balances():
    eth_balance = w3.eth.get_balance(addr)
    usdc_balance_across = usdc_contract.functions.balanceOf(ACROSS).call()
    usdc_balance = usdc_contract.functions.balanceOf(addr).call()
    return (
        f"Balances:\n"
        f"{eth_balance / 10**18} ETH in wallet\n"
        f"{usdc_balance / 10**6} USDC in wallet\n\n"
        f"Balance of Across:\n{usdc_balance_across / 10**6} USDC\n"
    )


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(get_balances()))
