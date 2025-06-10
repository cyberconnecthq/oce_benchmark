#!/usr/bin/env python3
"""
swap_eth_to_usdc.py

执行流程：
1) 把 0.1 ETH wrap 成 WETH
2) 批准 Uniswap V3 SwapRouter 花费该 WETH
3) 调用 exactInputSingle 以 0.05% 费率换成 USDC
4) 打印 swap 前后的余额
"""

import os, time, json
from decimal import Decimal
from web3 import Web3, HTTPProvider
from web3.types import (
    BlockIdentifier,
    EventData,
    StateOverride,
    TxParams,
    
)
from eth_account.signers.local import (
    LocalAccount,
)
# ─── 基本配置 ────────────────────────────────────────────────────────────────
RPC_URL =  "http://127.0.0.1:8545"
PRIVATE_KEY = os.getenv(
    "PRIV_KEY",
    # Anvil 默认首个账户
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
)
AMOUNT_IN_ETH = Decimal("0.1")      # 想换多少 ETH
FEE_TIER      = 500                # 0.05 %

# 合约地址
WETH  = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0E5C4F27eAD9083C756Cc2")
USDC  = Web3.to_checksum_address("0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")
ROUTER= Web3.to_checksum_address("0xE592427A0AEce92De3Edee1F18E0157C05861564")
QUOTER= Web3.to_checksum_address("0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6")  # Uniswap V3 Quoter

w3 = Web3(HTTPProvider(RPC_URL))
account:LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr    = account.address
print(f"Connected to {RPC_URL}, use account {addr}")

# ─── 最小 ABI（只保留用得到的函数）────────────────────────────────────────────
ERC20_ABI = json.loads("""[
  {"constant":true,"inputs":[{"name":"owner","type":"address"}],
   "name":"balanceOf","outputs":[{"name":"","type":"uint256"}],
   "stateMutability":"view","type":"function"},
  {"constant":false,"inputs":[
     {"name":"spender","type":"address"},
     {"name":"amount","type":"uint256"}],
   "name":"approve","outputs":[{"name":"","type":"bool"}],
   "stateMutability":"nonpayable","type":"function"}
]""")

WETH_ABI = json.loads("""[
  {"inputs":[],"name":"deposit","outputs":[],
   "stateMutability":"payable","type":"function"}
]""") + ERC20_ABI  # 复用 balanceOf/approve

ROUTER_ABI = json.loads("""[
  {"inputs":[{"components":[
     {"name":"tokenIn","type":"address"},
     {"name":"tokenOut","type":"address"},
     {"name":"fee","type":"uint24"},
     {"name":"recipient","type":"address"},
     {"name":"deadline","type":"uint256"},
     {"name":"amountIn","type":"uint256"},
     {"name":"amountOutMinimum","type":"uint256"},
     {"name":"sqrtPriceLimitX96","type":"uint160"}
  ],"name":"params","type":"tuple"}],
   "name":"exactInputSingle",
   "outputs":[{"name":"amountOut","type":"uint256"}],
   "stateMutability":"payable","type":"function"}
]""")

QUOTER_ABI = json.loads("""[
  {"inputs":[
     {"name":"tokenIn","type":"address"},
     {"name":"tokenOut","type":"address"},
     {"name":"fee","type":"uint24"},
     {"name":"amountIn","type":"uint256"},
     {"name":"sqrtPriceLimitX96","type":"uint160"}
  ],
   "name":"quoteExactInputSingle",
   "outputs":[{"name":"amountOut","type":"uint256"}],
   "stateMutability":"view","type":"function"}
]""")

weth   = w3.eth.contract(address=WETH,   abi=WETH_ABI)
usdc   = w3.eth.contract(address=USDC,   abi=ERC20_ABI)
router = w3.eth.contract(address=ROUTER, abi=ROUTER_ABI)
quoter = w3.eth.contract(address=QUOTER, abi=QUOTER_ABI)

def send(tx: TxParams):
    tx.update({
        "nonce": w3.eth.get_transaction_count(addr),
        "chainId": w3.eth.chain_id,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

def fmt(amount, decimals=18):
    return Decimal(amount) / Decimal(10**decimals)

# ─── 步骤 1：Wrap ETH → WETH ────────────────────────────────────────────────
amount_in_wei = int(AMOUNT_IN_ETH * 10**18)
print(f"\n1️⃣  deposit {AMOUNT_IN_ETH} ETH → WETH ...")
deposite_tx = weth.functions.deposit().build_transaction({
        "from":  addr,
        "value": amount_in_wei,
        "gas":   100_000
    })
print(deposite_tx)
receipt = send(
    deposite_tx
)
print("   done, gas used:", receipt.gasUsed)

# ─── 步骤 2：Approve Router ────────────────────────────────────────────────
print("2️⃣  approve Router to spend WETH ...")
approve_tx = weth.functions.approve(ROUTER, amount_in_wei).build_transaction({
        "from": addr,
        "gas":  80_000
    })
receipt = send(
    approve_tx
)
print(approve_tx)
print("   approved.")

# ─── 步骤 3：exactInputSingle swap WETH → USDC ─────────────────────────────
deadline = int(time.time()) + 600
params = (
    WETH, USDC, FEE_TIER, addr,  # tokenIn, tokenOut, fee, recipient
    deadline,                    # deadline
    amount_in_wei,               # amountIn
    0,                           # amountOutMinimum (演示用；生产请用预估*0.99)
    0                            # sqrtPriceLimitX96 (不设限制)
)

print("3️⃣  swap ...")
swap_tx = router.functions.exactInputSingle(params).build_transaction({
        "from":  addr,
        "value": 0,
        "gas":   300_000
    })
print(swap_tx)
receipt = send(
    swap_tx
)
print("   swap tx mined, gas used:", receipt.gasUsed)

# ─── 结果 ───────────────────────────────────────────────────────────────────
usdc_balance = usdc.functions.balanceOf(addr).call()
print(f"\n✅  USDC received: {fmt(usdc_balance, 6):,.2f} USDC")

# 查询ETH价格（通过Uniswap V3的Quoter合约）
def get_eth_price():
    # 这里以WETH/USDC池为例，查询1 ETH可兑换多少USDC
    amount_in_wei = 10**18  # 1 ETH
    
    try:
        # 使用Quoter合约查询价格
        usdc_out = quoter.functions.quoteExactInputSingle(
            WETH,           # tokenIn
            USDC,           # tokenOut  
            FEE_TIER,       # fee (500 = 0.05%)
            amount_in_wei,  # amountIn (1 ETH)
            0               # sqrtPriceLimitX96 (不设限制)
        ).call()
        
        price = Decimal(usdc_out) / Decimal(10**6)  # USDC有6位小数
        print(f"当前ETH价格约为: {price:,.2f} USDC")
        return price
        
    except Exception as e:
        print(f"获取价格失败: {e}")
        # 如果Quoter调用失败，可以尝试直接从池子获取价格信息
        print("尝试使用替代方法获取价格...")
        return get_eth_price_fallback()

def get_eth_price_fallback():
    """备用方法：通过计算池子储备量获取大概价格"""
    try:
        # 这里可以添加其他获取价格的方法
        # 比如从其他DEX或价格API获取
        print("备用价格获取方法未实现")
        return Decimal("0")
    except Exception as e:
        print(f"备用方法也失败了: {e}")
        return Decimal("0")

get_eth_price()