"""
Borrow 200 USDT from AAVE
"""

from evaluate_utils.aave_v3_util import supply_eth, borrow_usdt



def main():
    supply_eth(1)
    (borrow_usdt(2000))
