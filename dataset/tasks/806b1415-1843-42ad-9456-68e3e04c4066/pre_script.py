from evaluate_utils.common_util import wrap_eth_to_weth
from evaluate_utils.uniswap_v3_util import swap
from dataset.constants import PEPE_CONTRACT_ADDRESS_ETH, WETH_CONTRACT_ADDRESS_ETH
from web3 import Web3 
import asyncio

wrap_eth_to_weth(2)
swap(
    Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
    Web3.to_checksum_address(PEPE_CONTRACT_ADDRESS_ETH),
    int(1*1e18),
    0,
    10000
)








