from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import (
    WETH_CONTRACT_ADDRESS_ETH,
    MORPHO_CONTRACT_ADDRESS_ETH,
    RPC_URL,
    PRIVATE_KEY,
    USDT_CONTRACT_ADDRESS_ETH,
)
from evaluate_utils.morpho_util import morpho_contract

# Lido相关合约地址
STETH_CONTRACT_ADDRESS = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"
WSTETH_CONTRACT_ADDRESS = "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0"
LIDO_STAKING_ADDRESS = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"  # Lido staking contract, same as stETH

# 初始化 web3 和账户
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

WETH = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH)
MORPHO = Web3.to_checksum_address(MORPHO_CONTRACT_ADDRESS_ETH)
USDT = Web3.to_checksum_address(USDT_CONTRACT_ADDRESS_ETH)
STETH = Web3.to_checksum_address(STETH_CONTRACT_ADDRESS)
WSTETH = Web3.to_checksum_address(WSTETH_CONTRACT_ADDRESS)
LIDO = Web3.to_checksum_address(LIDO_STAKING_ADDRESS)

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

# stETH ABI, 只需totalSupply
STETH_ABI = ERC20_ABI + [
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

# wstETH ABI, 只需balanceOf
WSTETH_ABI = ERC20_ABI

# 获取合约实例
weth_contract = w3.eth.contract(address=WETH, abi=ERC20_ABI)
usdt_contract = w3.eth.contract(address=USDT, abi=ERC20_ABI)
steth_contract = w3.eth.contract(address=STETH, abi=STETH_ABI)
wsteth_contract = w3.eth.contract(address=WSTETH, abi=WSTETH_ABI)

async def get_balances():
    # 获取WETH和USDT余额
    wallet_weth = weth_contract.functions.balanceOf(addr).call()
    morpho_weth = weth_contract.functions.balanceOf(MORPHO).call()
    usdt_balance = usdt_contract.functions.balanceOf(addr).call()
    morpho_usdt_balance = usdt_contract.functions.balanceOf(MORPHO).call()

    # 获取Morpho position
    market_id = '0xb8fc70e82bc5bb53e773626fcc6a23f7eefa036918d7ef216ecfb1950a94a85e'
    supply_shares, borrow_shares, collateral = morpho_contract.functions.position(market_id, addr).call()

    # 获取stETH和wstETH余额
    steth_balance = steth_contract.functions.balanceOf(addr).call()
    wsteth_balance = wsteth_contract.functions.balanceOf(addr).call()
    # 查询Lido合约中的WETH余额
    lido_weth_balance = weth_contract.functions.balanceOf(LIDO).call()
    lido_eth_balance = w3.eth.get_balance(LIDO)

    # English comments for new Lido/stETH/wstETH info
    return (
        f"Current wallet ({addr}) WETH balance:\n"
        f"- {wallet_weth / 1e18} WETH\n"
        f"- {usdt_balance/1e6} USDT\n"
        f"- {steth_balance/1e18} stETH  # stETH balance in wallet\n"
        f"- {wsteth_balance/1e18} wstETH  # wstETH balance in wallet\n\n"
        f"Lido contract balance:\n"
        f"- {lido_weth_balance/1e18} WETH\n"
        f"- {lido_eth_balance/1e18} ETH\n"

        f"Morpho contract ({MORPHO}) balance:\n"
        f"- {morpho_weth / 1e18} WETH\n"
        f"- {morpho_usdt_balance/ 1e6} USDT\n\n"
        f"Account position:\n"
        f"- wstETH/WETH pair supply shares: {supply_shares}\n"
        f"- wstETH/WETH pair borrow shares: {borrow_shares}\n"
        f"- wstETH/WETH pair collateral: {collateral / 1e18} wstETH\n\n"

    )

if __name__ == '__main__':
    import asyncio
    print(asyncio.run(get_balances()))
