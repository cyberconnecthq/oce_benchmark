from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount



RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" #the first default anvil account
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address
receiver_addr = Web3.to_checksum_address("0xAd4C0379544aE7efd56F2B58c7ffcfD63A1cb216")

USDC  = Web3.to_checksum_address("0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")

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

usdc_contract = w3.eth.contract(address=USDC, abi=ERC20_ABI)


async def get_balances():
    eth_balance_sender = w3.eth.get_balance(addr)
    usdc_balance_sender = usdc_contract.functions.balanceOf(addr).call()
    usdc_balance_receiver = usdc_contract.functions.balanceOf(receiver_addr).call()
    return (
        f"Balances of sender:\n"
        f"{eth_balance_sender / 10**18} ETH\n"
        f"{usdc_balance_sender / 10**6} USDC\n"

        f"Balances of receiver:\n"
        f"{usdc_balance_receiver / 10**6} USDC\n"
    )


