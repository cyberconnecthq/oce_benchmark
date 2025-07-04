from web3 import Web3
from evaluate_utils.common_util import wrap_eth_to_weth, approve_erc20
from evaluate_utils.uniswap_v3_util import swap
from dataset.constants import (
    SKY_CONTRACT_ADDRESS_ETH,
    USDS_WRAPPER_ADDRESS_ETH,
    WETH_CONTRACT_ADDRESS_ETH,
    USDC_CONTRACT_ADDRESS_ETH,
    ACCOUNT_ADDRESS,
    USDS_CONTRACT_ADDRESS_ETH
)

def main():
    wrap_eth_to_weth(1)
    swap(
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
        int(0.01*1e18),
        0
    )
    approve_erc20(
        Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(SKY_CONTRACT_ADDRESS_ETH),
        int(1*1e6)
    )
    approve_erc20(
        Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(USDS_WRAPPER_ADDRESS_ETH),
        int(1*1e6)
    )

if __name__ == "__main__":
    main()