from web3 import Web3
from dataset.constants import (
    SUSDS_PROXY_ABI,
    USDS_CONTRACT_ADDRESS_ETH,
    USDS_PM_WRAPPER_ABI,
    USDS_WRAPPER_ADDRESS_ETH,
    USDC_CONTRACT_ADDRESS_ETH,
    WETH_CONTRACT_ADDRESS_ETH,
    SUSDE_CONTRACT_ADDRESS_ETH,
    SUSDS_PROXY_CONTRACT_ADDRESS_ETH,
    ERC20_ABI
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


w3 = Web3(HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

usds_wrapper = w3.eth.contract(
    address=Web3.to_checksum_address(USDS_WRAPPER_ADDRESS_ETH),
    abi=USDS_PM_WRAPPER_ABI
)

susds_proxy = w3.eth.contract(
    address=Web3.to_checksum_address(SUSDS_PROXY_CONTRACT_ADDRESS_ETH),
    abi=SUSDS_PROXY_ABI
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
    # print(receipt.values())
    return receipt.values()


def deposit_usds(amount_usds, receiver=None, referral=0):
    """
    调用USDS PM Wrapper合约的deposit方法，将USDS存入合约
    :param amount_usds: 存入的USDS数量（18位小数，float或int）
    :param receiver: 接收shares的地址，默认为当前账户
    :param referral: 推荐码，默认为0
    :return: 交易回执
    """
    # 获取USDS合约地址
    usds_addr = usds_wrapper.functions.usds().call()
    usds = w3.eth.contract(address=usds_addr, abi=ERC20_ABI)

    # USDS是18位小数
    amount = int(amount_usds * 1e18)
    if receiver is None:
        receiver = addr

    approve_tx = usds.functions.approve(
        Web3.to_checksum_address(SUSDS_PROXY_CONTRACT_ADDRESS_ETH),
        amount
    ).build_transaction({
        "from": addr,
        "nonce": w3.eth.get_transaction_count(addr),
        "gas": 100000,
        "gasPrice": w3.to_wei("20", "gwei")
    })
    signed_approve = w3.eth.account.sign_transaction(approve_tx, private_key=PRIVATE_KEY)
    approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
    w3.eth.wait_for_transaction_receipt(approve_hash)

    # 调用deposit
    tx = susds_proxy.functions.deposit(
        amount,
        Web3.to_checksum_address(receiver),
        int(referral)
    ).build_transaction({
        "from": addr,
        "nonce": w3.eth.get_transaction_count(addr),
        "gas": 300000,
        "gasPrice": w3.to_wei("20", "gwei")
    })
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"USDS存入交易已发送，哈希: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(receipt.values())
    return receipt.values()



def main():
    wrap_eth_to_weth(2)
    swap(
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
        int(2*1e18),
        0
    )

    approve_erc20(
        Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(USDS_WRAPPER_ADDRESS_ETH),
        int(1000*1e6)
    )
    swap_usdc_to_usds(
        10
    )
    deposit_usds(
        5
    )


if __name__ == "__main__":
    main()
