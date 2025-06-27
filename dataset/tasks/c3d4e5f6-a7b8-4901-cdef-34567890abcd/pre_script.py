from evaluate_utils.common_util import wrap_eth_to_weth
from evaluate_utils.uniswap_v3_util import swap
from dataset.constants import USDT_CONTRACT_ADDRESS_ETH, WETH_CONTRACT_ADDRESS_ETH
import asyncio
from web3 import Web3

wrap_eth_to_weth(1)
swap(
    Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH), 
    Web3.to_checksum_address(USDT_CONTRACT_ADDRESS_ETH), 
    int(1*1e18), 0, 10000)