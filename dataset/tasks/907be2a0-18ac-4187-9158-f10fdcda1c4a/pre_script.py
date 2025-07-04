"""
Build the state for task:'Borrow 120 USDT from Aave'
supply to aave v3 1 WETH
"""
from evaluate_utils.aave_v3_util import supply_eth


def main():
    print(supply_eth(1))
