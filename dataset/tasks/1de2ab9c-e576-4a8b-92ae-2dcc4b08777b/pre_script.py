from web3 import Web3
from evaluate_utils.common_util import wrap_eth_to_weth, approve_erc20
from evaluate_utils.uniswap_v3_util import swap_weth_to_usdc
from dataset.constants import (
    USDC_CONTRACT_ADDRESS_ETH,
    UNISWAP_V3_ROUTER_2_ADDRESS_ETH,
    UNISWAP_V3_ROUTER_ADDRESS_ETH,
    WETH_CONTRACT_ADDRESS_ETH
)

def main():
    wrap_eth_to_weth(0.01)
    swap_weth_to_usdc(0.01)
    approve_erc20(
        Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(UNISWAP_V3_ROUTER_2_ADDRESS_ETH),
        int(0.01*1e18)
    )
    approve_erc20(
        Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(UNISWAP_V3_ROUTER_ADDRESS_ETH),
        int(0.01*1e18)
    )

if __name__ == '__main__':
    main()