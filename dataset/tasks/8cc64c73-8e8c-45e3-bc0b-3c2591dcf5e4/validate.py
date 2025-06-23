from evaluate_utils.aave_v3_util import get_aave_info
from dataset.constants import PRIVATE_KEY, RPC_URL, USDT_CONTRACT_ADDRESS_ETH, WETH_CONTRACT_ADDRESS_ETH, ERC20_ABI
from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount

w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)

# Set up addresses and web3 provider
USDT = Web3.to_checksum_address(USDT_CONTRACT_ADDRESS_ETH)
WETH = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH)
usdt_contract = w3.eth.contract(address=USDT, abi=ERC20_ABI)
weth_contract = w3.eth.contract(address=WETH, abi=ERC20_ABI)

ADDRESS = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"

async def get_balances():
    # Get AAVE info
    aave_info = await get_aave_info(ADDRESS)
    # Get USDT balance
    usdt_balance = usdt_contract.functions.balanceOf(ADDRESS).call()
    # Get WETH balance
    weth_balance = weth_contract.functions.balanceOf(ADDRESS).call()
    return (
        f"Current wallet balance:\n"
        f"{usdt_balance / 10**6} USDT\n"
        f"{weth_balance / 10**18} WETH\n\n"
        f"{aave_info}"
    )

if __name__ == '__main__':
    import asyncio
    print(asyncio.run(get_balances()))