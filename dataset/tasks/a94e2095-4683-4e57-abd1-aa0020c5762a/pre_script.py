from web3 import Web3
from dataset.constants import (
    USDC_CONTRACT_ADDRESS_ETH,
    WETH_CONTRACT_ADDRESS_ETH,
    MORPHO_STEAKHOUSE_USDC_VAULT_ADDRESS_ETH,
    ACCOUNT_ADDRESS
)

from evaluate_utils.common_util import wrap_eth_to_weth
from evaluate_utils.uniswap_v3_util import swap
from evaluate_utils.morpho_util import deposit_to_vault

wrap_eth_to_weth(10)
swap(
    Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
    Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
    int(1*1e18),
    0
)
deposit_to_vault(
    vault_address=Web3.to_checksum_address(MORPHO_STEAKHOUSE_USDC_VAULT_ADDRESS_ETH),
    amount_usdc=0.5,
    receiver=Web3.to_checksum_address(ACCOUNT_ADDRESS),
)


    









