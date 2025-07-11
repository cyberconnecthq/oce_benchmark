from web3 import Web3
from dataset.constants import (
    USDC_CONTRACT_ADDRESS_ETH,
    WETH_CONTRACT_ADDRESS_ETH,
    MORPHO_STEAKHOUSE_USDC_VAULT_ADDRESS_ETH
)

from evaluate_utils.common_util import wrap_eth_to_weth, approve_erc20
from evaluate_utils.uniswap_v3_util import swap

def main():

    wrap_eth_to_weth(10)
    swap(
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
        int(1*1e18),
        0
    )
    approve_erc20(
        Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(MORPHO_STEAKHOUSE_USDC_VAULT_ADDRESS_ETH),
        int(5*1e6)
    )









if __name__ == '__main__':
    main()


