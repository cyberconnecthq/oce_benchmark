"""
Borrow 200 USDT from AAVE
"""

from evaluate_utils.aave_v3_util import supply_eth, borrow_token
from dataset.constants import USDC_CONTRACT_ADDRESS_ETH


if __name__ == '__main__':
    supply_eth(1)
    borrow_token(
        USDC_CONTRACT_ADDRESS_ETH,
        0.01,
        6,
        2,
        0
    )
