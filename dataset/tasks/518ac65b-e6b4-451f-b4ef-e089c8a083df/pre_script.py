from web3 import Web3
from dataset.constants import (
    USDS_CONTRACT_ADDRESS_ETH,
    USDS_WRAPPER_ADDRESS_ETH,
    USDC_CONTRACT_ADDRESS_ETH,
    WETH_CONTRACT_ADDRESS_ETH,
    SUSDE_CONTRACT_ADDRESS_ETH
)
from evaluate_utils.common_util import (
    wrap_eth_to_weth,
    approve_erc20
)
from evaluate_utils.uniswap_v3_util import swap


from web3 import HTTPProvider
import json
from dataset.constants import RPC_URL, PRIVATE_KEY

# 加载USDS PM Wrapper ABI
with open("abi/usds_pm_wrapper_abi.json", "r") as f:
    USDS_PM_WRAPPER_ABI = json.load(f)

w3 = Web3(HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

usds_wrapper = w3.eth.contract(
    address=Web3.to_checksum_address(USDS_WRAPPER_ADDRESS_ETH),
    abi=USDS_PM_WRAPPER_ABI
)

def swap_usdc_to_usds(amount_usdc):
    """
    使用USDS PM Wrapper合约的sellGem方法将USDC兑换为USDS
    :param amount_usdc: 兑换的USDC数量（6位小数，float或int）
    :return: 交易哈希
    """
    # USDC是6位小数
    amount = int(amount_usdc * 1e6)
    # 构建交易
    tx = usds_wrapper.functions.sellGem(
        addr,   # usr: 收款地址
        amount  # gemAmt: 卖出的USDC数量（单位: 6位小数）
    ).build_transaction({
        "from": addr,
        "nonce": w3.eth.get_transaction_count(addr),
        "gas": 300000,
        "gasPrice": w3.to_wei("20", "gwei")
    })
    # 签名并发送
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"USDC兑换USDS交易已发送，哈希: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(receipt.values())
    return receipt.values()


def main():
    wrap_eth_to_weth(1)
    swap(
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
        int(1*1e18),
        0
    )

    approve_erc20(
        Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(USDS_WRAPPER_ADDRESS_ETH),
        int(10*1e6)
    )
    swap_usdc_to_usds(
        5
    )


if __name__ == "__main__":
    main()
