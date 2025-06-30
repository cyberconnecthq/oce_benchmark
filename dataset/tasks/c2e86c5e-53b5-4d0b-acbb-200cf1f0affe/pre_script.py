#supply 1 WETH to aave

from evaluate_utils.aave_v3_util import supply_eth


if __name__ == '__main__':
    import asyncio
    supply_eth(3)