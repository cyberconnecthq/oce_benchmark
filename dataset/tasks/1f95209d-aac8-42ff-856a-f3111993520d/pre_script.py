#supply 1 WETH to aave

from dataset.constants import USDC_CONTRACT_ADDRESS_ETH
from evaluate_utils.aave_v3_util import supply_aave_v3_token


if __name__ == '__main__':
    supply_aave_v3_token(
        USDC_CONTRACT_ADDRESS_ETH,
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        1*10**6
    )