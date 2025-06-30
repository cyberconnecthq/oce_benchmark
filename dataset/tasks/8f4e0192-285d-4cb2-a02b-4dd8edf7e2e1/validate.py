from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import WETH_CONTRACT_ADDRESS_ETH, MORPHO_CONTRACT_ADDRESS_ETH, RPC_URL, PRIVATE_KEY, USDT_CONTRACT_ADDRESS_ETH
from evaluate_utils.morpho_util import morpho_contract

# 初始化 web3 和账户
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

WETH = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH)
MORPHO = Web3.to_checksum_address(MORPHO_CONTRACT_ADDRESS_ETH)
USDT = Web3.to_checksum_address(USDT_CONTRACT_ADDRESS_ETH)

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
usdt_contract = w3.eth.contract(address=USDT, abi=ERC20_ABI)

async def get_balances():
    wallet_weth = weth_contract.functions.balanceOf(addr).call()
    morpho_weth = weth_contract.functions.balanceOf(MORPHO).call()
    market_id = '0xdbffac82c2dc7e8aa781bd05746530b0068d80929f23ac1628580e27810bc0c5'
    supply_shares, borrow_shares, collateral = morpho_contract.functions.position(market_id, addr).call()
    usdt_balance = usdt_contract.functions.balanceOf(addr).call()
    morpho_usdt_balance = usdt_contract.functions.balanceOf(MORPHO).call()
    return (
        f"Current wallet ({addr}) WETH balance:\n"
        f"- {wallet_weth / 1e18} WETH\n"
        f"- {usdt_balance/1e6} USDT\n\n"
        f"Morpho contract ({MORPHO}) balance:\n"
        f"- {morpho_weth / 1e18} WETH\n"
        f"- {morpho_usdt_balance/ 1e6} USDT\n\n"
        f"Account position:\n"
        f"- WETH/USDT pair supply shares: {supply_shares}\n"
        f"- WETH/USDT pair borrow shares: {borrow_shares}\n"
        f"- WETH/USDT pair collateral: {collateral / 1e18} WETH\n"
    )
if __name__ == '__main__':
    import asyncio
    print(asyncio.run(get_balances()))
