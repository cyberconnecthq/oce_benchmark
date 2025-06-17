# supply 1 WETH to aave

from evaluate_utils.aave_v3_util import get_aave_info
from dataset.constants import USDT_CONTRACT_ADDRESS_ETH, ERC20_ABI
from web3 import Web3, HTTPProvider

USDT = Web3.to_checksum_address(USDT_CONTRACT_ADDRESS_ETH)
w3 = Web3(HTTPProvider("http://127.0.0.1:8545"))
usdt_contract = w3.eth.contract(address=USDT, abi=ERC20_ABI)


async def get_balances():
    aave_info = await get_aave_info("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")
    usdt_balance = usdt_contract.functions.balanceOf("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266").call()
    return (
        f"Current wallet balance:\n"
        f"{usdt_balance / 10**6} USDT\n\n"
        f"{aave_info}"
    )

if __name__ == '__main__':
    import asyncio
    print(asyncio.run(get_balances()))