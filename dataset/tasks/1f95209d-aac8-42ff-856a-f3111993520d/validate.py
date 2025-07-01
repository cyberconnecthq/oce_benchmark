# supply 1 WETH to aave

from evaluate_utils.aave_v3_util import get_aave_info
from dataset.constants import PRIVATE_KEY, RPC_URL, USDC_CONTRACT_ADDRESS_ETH, ERC20_ABI
from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount

w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)

USDC = Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH)
usdc_contract = w3.eth.contract(address=USDC, abi=ERC20_ABI)

async def get_balances():
    aave_info = await get_aave_info("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")
    usdc_balance = usdc_contract.functions.balanceOf("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266").call()
    return (
        f"Current wallet balance:\n"
        f"{usdc_balance / 10**6} USDC\n\n"
        f"{aave_info}"
    )

if __name__ == '__main__':
    import asyncio
    print(asyncio.run(get_balances()))