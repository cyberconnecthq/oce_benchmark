"""
Build the state for task:'Borrow 120 USDT from Aave'
supply to aave v3 1 WETH
"""
from evaluate_utils.aave_v3_util import supply_eth
from evaluate_utils.common_util import wrap_eth_to_weth


def main():
    wrap_eth_to_weth(10)
    supply_eth(1)

if __name__ == '__main__':
    main()
