"""
Stake 0.5 ETH 到 Lido（EIP-1559 交易）
-------------------------------------------
准备：
1. 安装依赖： pip install web3 eth-account
2. 把 PRIV_KEY 环境变量设为你的 EOA 私钥
3. 把 RPC_URL 换成主网 RPC（Infura/Alchemy/自建节点均可）
@swap.py 参考：本脚本直接复用 swap.py 的 RPC/account 读取方式
"""

import os, json, time
from decimal import Decimal
from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
def main():
    # 参考 swap.py 的用法
    RPC_URL =  "http://127.0.0.1:8545"

    PRIVATE_KEY = os.getenv(
        "PRIV_KEY",
        # Anvil 默认首个账户
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    )

    ETH_AMOUNT   = Decimal("1")        # 要质押的 ETH
    SEND_TX      =  True                # 为 True 时立刻广播

    LIDO_ADDR    = Web3.to_checksum_address("0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84")  # stETH 合约
    REFERRAL     = "0x0000000000000000000000000000000000000000"  # 无推荐人，可改

    # ---------------- minimal ABI (仅 submit) ---------------- #
    LIDO_ABI = json.loads("""
    [
    {"name":"submit","type":"function","stateMutability":"payable",
    "inputs":[{"name":"_referral","type":"address"}],
    "outputs":[{"name":"shares","type":"uint256"}]}
    ]
    """)

    w3 = Web3(HTTPProvider(RPC_URL))
    account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
    ACCOUNT = account.address
    print(f"连接到 {RPC_URL}, 使用账户 {ACCOUNT}")

    lido = w3.eth.contract(address=LIDO_ADDR, abi=LIDO_ABI)

    # ---------- 构造交易 ---------- #
    value_wei    = int(ETH_AMOUNT * 10**18)
    base_fee     = 3000
    max_priority = w3.to_wei("1.5", "gwei")           # 可调整
    max_fee      = base_fee * 2 + max_priority        # 简单策略：2×BaseFee

    tx = lido.functions.submit(REFERRAL).build_transaction({
        "from": ACCOUNT,
        "value": value_wei,
        "nonce": w3.eth.get_transaction_count(ACCOUNT),
        "gas": 200_000,                               # 可先 estimate_gas() 再加 buffer
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": max_priority,
        "chainId": w3.eth.chain_id
    })

    # ---------- 签名 & 可选广播 ---------- #
    print(tx)
    signed_tx  = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    raw_tx_hex = signed_tx.raw_transaction.hex()

    print("Raw tx ready:", raw_tx_hex)

    if SEND_TX:
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print("🎉 Sent!  Tx hash:", tx_hash.hex())
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print("Status:", receipt.status)