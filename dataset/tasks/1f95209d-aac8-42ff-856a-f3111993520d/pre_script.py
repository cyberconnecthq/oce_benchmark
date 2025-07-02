#supply 1 WETH to aave


from web3 import Web3
from evaluate_utils.common_util import approve_erc20, wrap_eth_to_weth
from evaluate_utils.uniswap_v3_util import swap
from evaluate_utils.aave_v3_util import supply_eth, borrow_token,supply_aave_v3_token
from dataset.constants import USDC_CONTRACT_ADDRESS_ETH, AAVE_POOL_ADDRESS_ETH, ACCOUNT_ADDRESS, WETH_CONTRACT_ADDRESS_ETH


if __name__ == '__main__':
    wrap_eth_to_weth(10)
    swap(
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
        int(0.01*1e18),
        0
    )
    supply_aave_v3_token(
        USDC_CONTRACT_ADDRESS_ETH,
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        1*10**6
    )