
#!/usr/bin/env python3
"""
validate.py

验证 Uniswap V3 swap 交易的执行
"""

import os
from web3 import Web3, HTTPProvider
from web3.types import TxParams
from eth_account.signers.local import LocalAccount

# ─── 基本配置 ────────────────────────────────────────────────────────────────
RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = os.getenv(
    "PRIV_KEY",
    # Anvil 默认首个账户
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
)

w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address
print(f"Connected to {RPC_URL}, use account {addr}")

# tx_list = [
#   {
#     "to": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
#     "value": 1000000000000000000,
#     "gas": 50000,
#     "gasPrice": 20000000000,
#     "nonce": 2357,
#     "chainId": 1,
#     "data": "0xd0e30db0"
#   },
#   {
#     "to": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
#     "value": 0,
#     "gas": 60000,
#     "gasPrice": 20000000000,
#     "nonce": 2358,
#     "chainId": 1,
#     "data": "0x095ea7b3000000000000000000000000E592427A0AEce92De3Edee1F18E0157C058615640000000000000000000000000000000000000000000000000de0b6b3a7640000"
#   },
#   {
#     "to": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
#     "value": 0,
#     "gas": 200000,
#     "gasPrice": 20000000000,
#     "nonce": 2359,
#     "chainId": 1,
#     "data": "0x414bf389000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000a0b86a33e6411e35e804931b04da73bd66e7a660000000000000000000000000000000000000000000000000000000000000bb8000000000000000000000000faafe5fcac0e87d40017e44cd462398026a1223000000000000000000000000000000000000000000000000000000000684280490000000000000000000000000000000000000000000000000de0b6b3a764000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
#   }
# ]
nonce = w3.eth.get_transaction_count(addr)
tx_list = [
    {
        "to": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "value": 0,
        "gas": 60000,
        "maxFeePerGas": 50000000000,
        "maxPriorityFeePerGas": 2000000000,
        "nonce": nonce,
        "data": "0x095ea7b3000000000000000000000000E592427A0AEce92De3Edee1F18E0157C0586156400000000000000000000000000000000000000000000000DE0B6B3A7640000",
        "chainId": 1
    },
    {
        "to": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "value": 0,
        "gas": 60000,
        "maxFeePerGas": 50000000000,
        "maxPriorityFeePerGas": 2000000000,
        "nonce": nonce + 1,
        "data": "0x095ea7b3000000000000000000000000E592427A0AEce92De3Edee1F18E0157C0586156400000000000000000000000000000000000000000000000DE0B6B3A7640000",
        "chainId": 1
    },
    {
        "to": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "value": 0,
        "gas": 300000,
        "maxFeePerGas": 50000000000,
        "maxPriorityFeePerGas": 2000000000,
        "nonce": nonce + 2,
        "data": "0x04e45aaf000000000000000000000000c02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb480000000000000000000000000000000000000000000000000000000000000bb80000000000000000000000000FAafe5FcaC0E87D40017E44CD462398026a122300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000de0b6b3a764000000000000000000000000000000000000000000000000000000000000000000000",
        "chainId": 1
    }
]

def send(tx: TxParams):

    sign_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(sign_tx.raw_transaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(tx_receipt)
    if tx_receipt.status == 1:
        print("交易执行成功!")
        print(f"使用的 gas: {tx_receipt.gasUsed}")
        print(f"区块号: {tx_receipt.blockNumber}")
    else:
        print("交易执行失败!")
        print(f"交易哈希: {tx_receipt.transactionHash.hex()}")
    return tx_receipt

for tx in tx_list:
    send(tx)
