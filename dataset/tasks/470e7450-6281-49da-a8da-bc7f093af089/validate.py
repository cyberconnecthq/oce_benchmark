from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import WETH_CONTRACT_ADDRESS_ETH, MORPHO_CONTRACT_ADDRESS_ETH, RPC_URL, PRIVATE_KEY
from evaluate_utils.morpho_util import morpho_contract

# 初始化 web3 和账户
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

WETH = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH)
MORPHO = Web3.to_checksum_address(MORPHO_CONTRACT_ADDRESS_ETH)

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

# 获取WETH合约实例
weth_contract = w3.eth.contract(address=WETH, abi=ERC20_ABI)

async def get_balances():
    wallet_weth = weth_contract.functions.balanceOf(addr).call()
    morpho_weth = weth_contract.functions.balanceOf(MORPHO).call()
    return (
        f"Current wallet ({addr}) WETH balance: {wallet_weth / 1e18} WETH\n"
        f"Morpho contract ({MORPHO}) WETH balance: {morpho_weth / 1e18} WETH"
    )

if __name__ == '__main__':
    import asyncio
    print(asyncio.run(get_balances()))
