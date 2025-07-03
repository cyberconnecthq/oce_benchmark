from evaluate_utils.common_util import wrap_eth_to_weth
from evaluate_utils.uniswap_v3_util import swap_weth_to_usdc

def main():
    wrap_eth_to_weth(0.01)
    swap_weth_to_usdc(0.01)

if __name__ == '__main__':
    main()