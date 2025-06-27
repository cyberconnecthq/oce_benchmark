"""
Borrow 200 USDT from AAVE
"""

from evaluate_utils.aave_v3_util import supply_eth, borrow_usdt



if __name__ == '__main__':
    supply_eth(1)
    borrow_usdt(200)
