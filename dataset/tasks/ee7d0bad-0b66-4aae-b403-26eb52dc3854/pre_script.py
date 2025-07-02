"""
Borrow 200 USDT from AAVE
"""

from web3 import Web3
from evaluate_utils.common_util import approve_erc20
from evaluate_utils.aave_v3_util import supply_eth, borrow_token
from dataset.constants import USDC_CONTRACT_ADDRESS_ETH, AAVE_POOL_ADDRESS_ETH


if __name__ == '__main__':
    supply_eth(1)
    approve_erc20(
        Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(AAVE_POOL_ADDRESS_ETH),
        int(1000*1e6)
    )
    borrow_token(
        USDC_CONTRACT_ADDRESS_ETH,
        0.01,
        6,
        2,
        0
    )
