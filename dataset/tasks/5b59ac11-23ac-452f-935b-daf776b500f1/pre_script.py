from web3 import Web3
from dataset.constants import USDT_CONTRACT_ADDRESS_ETH, WETH_CONTRACT_ADDRESS_ETH
from evaluate_utils.common_util import wrap_eth_to_weth, approve_erc20
from evaluate_utils.morpho_util import borrow_usdt_from_morpho, supply_weth_to_morpho
from dataset.constants import (
    MORPHO_GENERAL_ADAPTER_ADDRESS_ETH,
    MORPHO_CONTRACT_ADDRESS_ETH,
    USDT_CONTRACT_ADDRESS_ETH
)

def main():
    addr =  Web3.to_checksum_address("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")
    market_params = (
        Web3.to_checksum_address(USDT_CONTRACT_ADDRESS_ETH),  # loanToken
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),  # collateralToken
        "0xe9eE579684716c7Bb837224F4c7BeEfA4f1F3d7f",         # oracle
        "0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC",         # irm
        915000000000000000                                   # lltv
    )
    wrap_eth_to_weth(2)
    approve_erc20(
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(MORPHO_GENERAL_ADAPTER_ADDRESS_ETH),
        1*10**18
    )

    approve_erc20(
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(MORPHO_CONTRACT_ADDRESS_ETH),
        1*10**18
    )

    market_params = (
        Web3.to_checksum_address(USDT_CONTRACT_ADDRESS_ETH),  # loanToken 
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),  # collateralToken
        "0xe9eE579684716c7Bb837224F4c7BeEfA4f1F3d7f",         # oracle
        "0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC",         # irm
        915000000000000000                                   # lltv
    )
    supply_weth_to_morpho(int(0.2*1e18), addr, market_params)
    borrow_usdt_from_morpho(
        int(1 * 1e6),
        addr,
        market_params
    )
    
    approve_erc20(
        Web3.to_checksum_address(USDT_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(MORPHO_CONTRACT_ADDRESS_ETH),
        int(100*1e6)
    )

if __name__ == '__main__':
    main()