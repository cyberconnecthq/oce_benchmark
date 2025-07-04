from evaluate_utils.common_util import wrap_eth_to_weth
from evaluate_utils.uniswap_v3_util import swap_weth_to_usdc, swap

from dataset.constants import (
    USDT_CONTRACT_ADDRESS_ETH,
    USDC_CONTRACT_ADDRESS_ETH,
    WETH_CONTRACT_ADDRESS_ETH
)
from web3 import Web3

def main():
    wrap_eth_to_weth(10)
    swap(
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(USDT_CONTRACT_ADDRESS_ETH),
        int(1*1e18),
        0
    )

