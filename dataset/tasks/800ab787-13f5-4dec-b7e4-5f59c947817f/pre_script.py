from evaluate_utils.morpho_util import supply_weth_to_morpho, approve_weth_to_morpho
from evaluate_utils.common_util import wrap_eth_to_weth
from web3 import Web3
import asyncio

addr =  Web3.to_checksum_address("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")

asyncio.run(wrap_eth_to_weth(2))
approve_weth_to_morpho(int(2*1e18), addr)
supply_weth_to_morpho(int(2*1e18), addr)
