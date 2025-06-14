# 将2个ETH包装成WETH
from evaluate_utils.common_util import wrap_eth_to_weth

if __name__ == '__main__':
    import asyncio
    asyncio.run(wrap_eth_to_weth(2))
