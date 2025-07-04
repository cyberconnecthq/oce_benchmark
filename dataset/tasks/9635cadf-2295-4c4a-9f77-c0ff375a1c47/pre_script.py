#!/usr/bin/env python3
# Stake 1 ETH via Lido wstETH wrapper and verify balance

import os, time, json
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

from dataset.constants import (
    WSTETH_CONTRACT_ADDRESS_ETH,
    RPC_URL,
    PRIVATE_KEY,
)
def main():
    load_dotenv()                                      # 如果你用 .env 保存 RPC/私钥
    OWNER       = Account.from_key(PRIVATE_KEY).address

    WSTETH = Web3.to_checksum_address(WSTETH_CONTRACT_ADDRESS_ETH)

    # ————————————————————————————————————————————————————————————————
    # 1) 初始化 Web3 & 最简 ERC-20 ABI（只需 balanceOf/decimals）
    # ————————————————————————————————————————————————————————————————
    w3 = Web3(Web3.HTTPProvider(RPC_URL))

    ERC20_ABI = json.loads("""[
    {"constant":true,"inputs":[{"name":"owner","type":"address"}],
    "name":"balanceOf","outputs":[{"name":"","type":"uint256"}],
    "stateMutability":"view","type":"function"},
    {"constant":true,"inputs":[],"name":"decimals",
    "name":"decimals","outputs":[{"name":"","type":"uint8"}],
    "stateMutability":"view","type":"function"}
    ]""")
    wsteth = w3.eth.contract(address=WSTETH, abi=ERC20_ABI)

    # ————————————————————————————————————————————————————————————————
    # 2) 记录质押前 wstETH 余额
    # ————————————————————————————————————————————————————————————————
    decimals   = wsteth.functions.decimals().call()
    bal_before = wsteth.functions.balanceOf(OWNER).call()
    print(f"wstETH before = {bal_before / 10**decimals:.6f}")

    # ————————————————————————————————————————————————————————————————
    # 3) 构造裸转账：把 1 ETH 直接发送到 wstETH 合约
    # ————————————————————————————————————————————————————————————————
    tx = {
        "from":   OWNER,
        "to":     WSTETH,
        "value":  w3.to_wei(1, "ether"),               # 1 ETH
        "nonce":  w3.eth.get_transaction_count(OWNER),
        "gas":    320_000,                            # 足够触发 submit + mint
        "maxFeePerGas":       w3.to_wei("30", "gwei"),
        "maxPriorityFeePerGas": w3.to_wei("1.5", "gwei"),
        "chainId": 1
    }
    signed = Account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print("⏳  staking tx sent →", w3.to_hex(tx_hash))

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(receipt.values())