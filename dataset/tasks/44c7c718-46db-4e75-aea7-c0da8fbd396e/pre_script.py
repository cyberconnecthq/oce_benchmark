from web3 import Web3
from evaluate_utils.common_util import wrap_eth_to_weth, approve_erc20
from evaluate_utils.uniswap_v3_util import swap
from dataset.constants import (
    WETH_CONTRACT_ADDRESS_ETH,
    USDC_CONTRACT_ADDRESS_ETH,
    ACCOUNT_ADDRESS,
    USDS_CONTRACT_ADDRESS_ETH
)


wrap_eth_to_weth(1)
swap(
    Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
    Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
    int(0.01*1e18),
    0
)
approve_erc20(
    
)