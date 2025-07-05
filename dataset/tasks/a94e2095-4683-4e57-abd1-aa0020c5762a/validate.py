from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import (
    WETH_CONTRACT_ADDRESS_ETH,
    MORPHO_CONTRACT_ADDRESS_ETH,
    RPC_URL,
    PRIVATE_KEY,
    USDC_CONTRACT_ADDRESS_ETH,
    MORPHO_STEAKHOUSE_USDC_VAULT_ADDRESS_ETH
)
from evaluate_utils.morpho_util import morpho_contract

# 初始化 web3 和账户
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

WETH = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH)
MORPHO = Web3.to_checksum_address(MORPHO_CONTRACT_ADDRESS_ETH)
USDC = Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH)

# ERC20 ABI，仅需 balanceOf
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

# Get WETH contract instance
weth_contract = w3.eth.contract(address=WETH, abi=ERC20_ABI)
usdc_contract = w3.eth.contract(address=USDC, abi=ERC20_ABI)
steakhouse_vault_addr = Web3.to_checksum_address(MORPHO_STEAKHOUSE_USDC_VAULT_ADDRESS_ETH)
steakhouse_vault_contract = w3.eth.contract(address=steakhouse_vault_addr, abi=ERC20_ABI)

async def get_balances():
    # Get wallet USDC balance
    usdc_balance = usdc_contract.functions.balanceOf(addr).call()
    # Get Steakhouse USDC Vault contract USDC balance
    steakhouse_usdc_balance = steakhouse_vault_contract.functions.balanceOf(addr).call()
    return (
        f"Current wallet balance:\n"
        f"- {usdc_balance / 1000000} USDC\n\n"
        f"- {steakhouse_usdc_balance / (10**18)} stUSDC\n"
    )



if __name__ == '__main__':
    import asyncio
    print(asyncio.run(get_balances()))
