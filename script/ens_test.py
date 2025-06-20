#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Register ‘caibai.eth’ for 1 year via ENS ETHRegistrarController
"""

import os, time, secrets, json
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
from dataset.constants import RPC_URL, PRIVATE_KEY    # ← 你的常量文件

temp_acct = Account.create()
ENS_OWNER = Web3.to_checksum_address("0xcCb30F16d38424F7a546944F0cf5EF8F2d116F70")


# ─────────────────────────────────────────────────────────────────────────────
# 0) 基本配置
# ─────────────────────────────────────────────────────────────────────────────
NAME     = "caiba-ai"                 # ⚠️ 只含 a-z0-9-
DURATION = 31_556_952               # 1 年
SECRET   = Web3.to_bytes(secrets.token_bytes(32))

RESOLVER = Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
DATA, REVERSE, FUSES = [], False, 0

CONTROLLER = Web3.to_checksum_address("0x253553366Da8546fC250F225fe3d25d0C782303b")

with open("./abi/ens_register_controller_abi.json") as f:
    CONTROLLER_ABI = json.load(f)

# ─────────────────────────────────────────────────────────────────────────────
# 1) 初始化 web3
# ─────────────────────────────────────────────────────────────────────────────
w3    = Web3(Web3.HTTPProvider(RPC_URL))
acct  = Account.from_key(PRIVATE_KEY)
OWNER = acct.address

ctrl = w3.eth.contract(address=CONTROLLER, abi=CONTROLLER_ABI)

# ─────────────────────────────────────────────────────────────────────────────
# 2) 预检查：valid + available
# ─────────────────────────────────────────────────────────────────────────────
if not ctrl.functions.valid(NAME).call():
    raise ValueError("❌  域名含非法字符，请只用 a-z0-9- 或 punycode")

if not ctrl.functions.available(NAME).call():
    raise ValueError("❌  该域名已被注册或处于赎回期")

price = ctrl.functions.rentPrice(NAME, DURATION).call()
fee   = price[0] + price[1]
print(f"注册 {NAME}.eth 一年需 {w3.from_wei(fee, 'ether')} ETH")

# ─────────────────────────────────────────────────────────────────────────────
# 3) commit
# ─────────────────────────────────────────────────────────────────────────────
commitment = ctrl.functions.makeCommitment(
    NAME, ENS_OWNER, DURATION, SECRET, RESOLVER, DATA, REVERSE, FUSES
).call()

nonce = w3.eth.get_transaction_count(OWNER)

tx = ctrl.functions.commit(commitment).build_transaction({
    "from":  OWNER,
    "nonce": nonce,
    "gas":   80_000,
    "maxFeePerGas":        w3.to_wei("25", "gwei"),
    "maxPriorityFeePerGas": w3.to_wei("1.5", "gwei"),
    "chainId": 1
})
signed = acct.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)   # ← 大写 T
print("commit  →", w3.to_hex(tx_hash))
recipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(recipt.values())

print("等待 60 s 的 minCommitmentAge…")
# time.sleep(65)
w3.provider.make_request("evm_increaseTime", [61])  # 向前跳 61 秒
w3.provider.make_request("evm_mine", [])           # 立刻产一个新块
# ─────────────────────────────────────────────────────────────────────────────
# 4) register
# ─────────────────────────────────────────────────────────────────────────────
nonce += 1
tx = ctrl.functions.register(
    NAME, ENS_OWNER, DURATION, SECRET, RESOLVER, DATA, REVERSE, FUSES
).build_transaction({
    "from":  OWNER,
    "nonce": nonce,
    "value": fee,
    "gas":   350_000,
    # "maxFeePerGas":        w3.to_wei("25", "gwei"),
    # "maxPriorityFeePerGas": w3.to_wei("1.5", "gwei"),
    "chainId": 1
})
signed = acct.sign_transaction(tx)
# w3.eth.simulate_v1(signed.raw_transaction)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print("register →", w3.to_hex(tx_hash))
rcpt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(rcpt.values())
print(f"✅  {NAME}.eth 已注册！区块: {rcpt.blockNumber}")