"""
Borrow 200 USDT from AAVE
"""

from evaluate_utils.aave_v3_util import supply_eth, borrow_usdt



if __name__ == '__main__':
    import asyncio
    asyncio.run(supply_eth(1))
    asyncio.run(borrow_usdt(2000))
