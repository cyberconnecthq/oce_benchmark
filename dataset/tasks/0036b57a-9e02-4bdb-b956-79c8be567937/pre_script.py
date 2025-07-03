from web3 import Web3
from evaluate_utils.common_util import wrap_eth_to_weth, approve_erc20
from dataset.constants import (
    WETH_CONTRACT_ADDRESS_ETH,
    USDC_CONTRACT_ADDRESS_ETH,
    ACCOUNT_ADDRESS,
    UNISWAP_V3_ROUTER_2_ADDRESS_ETH,
    UNISWAP_V3_ROUTER_ADDRESS_ETH
)

def main():
    wrap_eth_to_weth(0.01)
    # 授权Uniswap V3两个路由合约可以使用10 WETH
    approve_erc20(
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(UNISWAP_V3_ROUTER_2_ADDRESS_ETH),
        10
    )
    approve_erc20(
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(UNISWAP_V3_ROUTER_ADDRESS_ETH),
        10
    )


if __name__ == '__main__':
    main()