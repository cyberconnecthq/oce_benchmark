from evaluate_utils.common_util import wrap_eth_to_weth,approve_erc20
from evaluate_utils.uniswap_v3_util import swap

from dataset.constants import (
    USDC_CONTRACT_ADDRESS_ETH,
    WETH_CONTRACT_ADDRESS_ETH,
    AAVE_POOL_ADDRESS_ETH
)
from web3 import Web3
wrap_eth_to_weth(10)
swap(
    Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
    Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
    int(1*1e18),
    0
)

approve_erc20(
    Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
    Web3.to_checksum_address(AAVE_POOL_ADDRESS_ETH),
    int(10*1e6)
)