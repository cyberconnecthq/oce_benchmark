from web3 import Web3
from dataset.constants import USDT_CONTRACT_ADDRESS_ETH, WETH_CONTRACT_ADDRESS_ETH
from evaluate_utils.common_util import wrap_eth_to_weth
from evaluate_utils.morpho_util import borrow_usdt_from_morpho
import asyncio
addr =  Web3.to_checksum_address("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")
market_params = (
    Web3.to_checksum_address(USDT_CONTRACT_ADDRESS_ETH),  # loanToken
    Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),  # collateralToken
    "0xe9eE579684716c7Bb837224F4c7BeEfA4f1F3d7f",         # oracle
    "0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC",         # irm
    915000000000000000                                   # lltv
)
asyncio.run(wrap_eth_to_weth(2))
borrow_usdt_from_morpho(
    int(1000 * 1e6),
    addr,
    market_params
)