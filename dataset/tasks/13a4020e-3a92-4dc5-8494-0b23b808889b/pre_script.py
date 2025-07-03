from web3 import Web3
from evaluate_utils.common_util import wrap_eth_to_weth, approve_erc20
from evaluate_utils.uniswap_v3_util import swap_weth_to_usdc
from dataset.constants import (
    USDC_CONTRACT_ADDRESS_ETH,
    WETH_CONTRACT_ADDRESS_ETH,
    ACCOUNT_ADDRESS,
    UNISWAP_NPM_ADDRESS_ETH
)

def main():
    wrap_eth_to_weth(0.01)
    swap_weth_to_usdc(0.005)

    approve_erc20(
        Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(UNISWAP_NPM_ADDRESS_ETH),
        int(5000*1e6)
    )

    approve_erc20(
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(UNISWAP_NPM_ADDRESS_ETH),
        int(0.1*1e18)
    )

if __name__ == '__main__':
    main()
