# 将2个ETH包装成WETH
from web3 import Web3
from evaluate_utils.common_util import wrap_eth_to_weth
from evaluate_utils.uniswap_v3_util import swap
from dataset.constants import (
    WETH_CONTRACT_ADDRESS_ETH,
    USDC_CONTRACT_ADDRESS_ETH,
    ACCOUNT_ADDRESS,
    SUSDE_CONTRACT_ADDRESS_ETH
)

if __name__ == '__main__':
    wrap_eth_to_weth(2)
    swap(
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(SUSDE_CONTRACT_ADDRESS_ETH),
        int(0.5*1e18),
        0
    )
