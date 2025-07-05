from web3 import Web3
from evaluate_utils.common_util import wrap_eth_to_weth
from evaluate_utils.common_util import approve_erc20
from dataset.constants import (
    WETH_CONTRACT_ADDRESS_ETH,
    MORPHO_CONTRACT_ADDRESS_ETH,
    MORPHO_GENERAL_ADAPTER_ADDRESS_ETH,
    ACCOUNT_ADDRESS
)
def main():
    wrap_eth_to_weth(1)
    approve_erc20(
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(MORPHO_CONTRACT_ADDRESS_ETH),
        10*10**6
    )
    approve_erc20(
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(MORPHO_GENERAL_ADAPTER_ADDRESS_ETH),
        10*10**6
    )