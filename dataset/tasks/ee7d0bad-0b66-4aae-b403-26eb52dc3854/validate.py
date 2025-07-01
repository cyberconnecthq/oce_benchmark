from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import USDC_CONTRACT_ADDRESS_ETH, WETH_CONTRACT_ADDRESS_ETH, RPC_URL, PRIVATE_KEY
from evaluate_utils.aave_v3_util import get_aave_info


w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

USDC = Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH)

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
weth_contract = w3.eth.contract(address=Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH), abi=ERC20_ABI)


async def get_balances():
    # 获取USDC余额
    usdc_balance = usdc_contract.functions.balanceOf(addr).call()
    
    aave_info = await get_aave_info(addr)
    
    return (
        f"当前钱包余额:\n"
        f"{usdc_balance / 10**6} USDC\n\n"
        f"{aave_info}"
    )


if __name__ == '__main__':
    import asyncio
    print(asyncio.run(get_balances()))