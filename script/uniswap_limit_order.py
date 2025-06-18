#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create a limit-sell order (WETH → USDC at 3000 USDC/WETH) on Uniswap V3
and verify the position NFT balance.
"""

import os, math, json, time
from decimal import Decimal
from web3 import Web3
from eth_account import Account
from dataset.constants import PRIVATE_KEY, RPC_URL, WETH_CONTRACT_ADDRESS_ETH, USDC_CONTRACT_ADDRESS_ETH, UNISWAP_NPM_ADDRESS_ETH

###############################################################################
# 1) 用户配置：RPC、私钥、数量等
###############################################################################
ACCOUNT      = Account.from_key(PRIVATE_KEY)
OWNER        = ACCOUNT.address

AMOUNT_WETH  = Decimal("0.1")                    # 要卖出的 WETH 数量
TARGET_PRICE = Decimal("3000")                   # 1 WETH = 3000 USDC

# 合约地址
WETH  = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH)
USDC  = Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH)
NFPM  = Web3.to_checksum_address(UNISWAP_NPM_ADDRESS_ETH)  # NonfungiblePositionManager
FEE   = 500                                   # 0.05 % pool

# 验证token顺序：USDC < WETH（按地址排序）
print(f"USDC: {USDC}")
print(f"WETH: {WETH}")
print(f"Token0 (smaller): {'USDC' if USDC < WETH else 'WETH'}")
print(f"Token1 (larger): {'WETH' if USDC < WETH else 'USDC'}")

###############################################################################
# 2) 载入 ABI（只保留必须函数，节省空间）
###############################################################################
ERC20_ABI = json.loads("""[
  {"constant":false,"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],
   "name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
  {"constant":true,"inputs":[{"name":"owner","type":"address"}],
   "name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"constant":true,"inputs":[],"name":"decimals",
   "outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"}
]""")

NFPM_ABI = json.loads("""[
  {"inputs":[{"components":[
     {"internalType":"address","name":"token0","type":"address"},
     {"internalType":"address","name":"token1","type":"address"},
     {"internalType":"uint24","name":"fee","type":"uint24"},
     {"internalType":"int24","name":"tickLower","type":"int24"},
     {"internalType":"int24","name":"tickUpper","type":"int24"},
     {"internalType":"uint256","name":"amount0Desired","type":"uint256"},
     {"internalType":"uint256","name":"amount1Desired","type":"uint256"},
     {"internalType":"uint256","name":"amount0Min","type":"uint256"},
     {"internalType":"uint256","name":"amount1Min","type":"uint256"},
     {"internalType":"address","name":"recipient","type":"address"},
     {"internalType":"uint256","name":"deadline","type":"uint256"}],
    "internalType":"struct INonfungiblePositionManager.MintParams",
    "name":"params","type":"tuple"}],
   "name":"mint","outputs":[
     {"internalType":"uint256","name":"tokenId","type":"uint256"},
     {"internalType":"uint128","name":"liquidity","type":"uint128"},
     {"internalType":"uint256","name":"amount0","type":"uint256"},
     {"internalType":"uint256","name":"amount1","type":"uint256"}],
   "stateMutability":"payable","type":"function"},
  {"constant":true,"inputs":[{"name":"owner","type":"address"}],
   "name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"constant":true,"inputs":[{"name":"tokenId","type":"uint256"}],
   "name":"positions","outputs":[
      {"name":"nonce","type":"uint96"},{"name":"operator","type":"address"},
      {"name":"token0","type":"address"},{"name":"token1","type":"address"},
      {"name":"fee","type":"uint24"},{"name":"tickLower","type":"int24"},
      {"name":"tickUpper","type":"int24"},{"name":"liquidity","type":"uint128"},
      {"name":"feeGrowthInside0LastX128","type":"uint256"},
      {"name":"feeGrowthInside1LastX128","type":"uint256"},
      {"name":"tokensOwed0","type":"uint128"},{"name":"tokensOwed1","type":"uint128"}],
   "stateMutability":"view","type":"function"},
  {"anonymous":false,"inputs":[{"indexed":true,"name":"from","type":"address"},
   {"indexed":true,"name":"to","type":"address"},{"indexed":true,"name":"tokenId","type":"uint256"}],
   "name":"Transfer","type":"event"}
]""")

###############################################################################
# 3) 计算 tick 区间（单-tick 宽度）
###############################################################################
TICK_SPACING = 10           # 0.05 % 池固定

def price_to_tick_correct(usdc_per_weth: Decimal) -> int:
    """
    正确的价格转tick计算
    
    在USDC/WETH池中：
    - USDC 是 token0 (地址较小)
    - WETH 是 token1 (地址较大)
    - Uniswap V3 价格 = token1/token0 = WETH/USDC
    
    如果 1 WETH = 3000 USDC：
    - 价格 = WETH/USDC = 1/3000 = 0.000333... (token1/token0)
    - 考虑小数位差异：WETH(18位) vs USDC(6位)
    - 调整后的价格 = (1 * 10^18) / (3000 * 10^6) = 10^12/3000
    """
    # WETH/USDC 比率（token1/token0）
    weth_per_usdc = Decimal(1) / usdc_per_weth
    
    # 调整小数位差异: WETH(18位) - USDC(6位) = 12位
    adjusted_price = weth_per_usdc * Decimal(10)**12
    
    # 计算tick: price = 1.0001^tick
    tick = int(math.log(float(adjusted_price)) / math.log(1.0001))
    
    # 对齐到spacing
    return (tick // TICK_SPACING) * TICK_SPACING

tick_lower = price_to_tick_correct(TARGET_PRICE)
tick_upper = tick_lower + TICK_SPACING           # 1 tick 宽度

print(f"\nTarget price 3000 USDC/WETH")
print(f"WETH/USDC price = {1/TARGET_PRICE:.6f}")
print(f"Adjusted price (considering decimals) = {(1/TARGET_PRICE) * (10**12):.0f}")
print(f"Calculated tick range: [{tick_lower}, {tick_upper}]")

###############################################################################
# 4) 铸造头寸 NFT
###############################################################################
w3    = Web3(Web3.HTTPProvider(RPC_URL))
weth  = w3.eth.contract(address=WETH, abi=ERC20_ABI)
nfpm  = w3.eth.contract(address=NFPM, abi=NFPM_ABI)

# 确定正确的token顺序和amount
if USDC < WETH:
    # USDC是token0, WETH是token1
    token0, token1 = USDC, WETH
    amount0_desired = 0  # 不提供USDC（限价卖单只提供WETH）
    amount1_desired = int(AMOUNT_WETH * (10**18))  # WETH数量
    print(f"\nToken0 (USDC): {token0}")
    print(f"Token1 (WETH): {token1}")
    print(f"Amount0 (USDC): {amount0_desired}")
    print(f"Amount1 (WETH): {amount1_desired}")
else:
    # WETH是token0, USDC是token1
    token0, token1 = WETH, USDC
    amount0_desired = int(AMOUNT_WETH * (10**18))  # WETH数量
    amount1_desired = 0  # 不提供USDC
    print(f"\nToken0 (WETH): {token0}")
    print(f"Token1 (USDC): {token1}")
    print(f"Amount0 (WETH): {amount0_desired}")
    print(f"Amount1 (USDC): {amount1_desired}")

# 4-1) 先给 NFPM 授权 WETH
max_amount = max(amount0_desired, amount1_desired)
nonce   = w3.eth.get_transaction_count(OWNER)
approve_tx = weth.functions.approve(NFPM, max_amount*2).build_transaction({
    "from": OWNER,
    "nonce": nonce,
    "gas": 120_000,
    "maxFeePerGas": w3.to_wei(30, "gwei"),
    "maxPriorityFeePerGas": w3.to_wei(1.5, "gwei"),
    "chainId": 1
})
signed  = ACCOUNT.sign_transaction(approve_tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print("Approve sent:", w3.to_hex(tx_hash))
w3.eth.wait_for_transaction_receipt(tx_hash)

# 4-2) MintParams
params = (
    token0, token1,                 # 正确的token顺序
    FEE,
    tick_lower, tick_upper,
    amount0_desired, amount1_desired,  # 对应的amount
    0, 0,                          # slippage min (可以设为0因为是单边流动性)
    OWNER,
    int(time.time()) + 600
)

nonce  += 1
mint_tx = nfpm.functions.mint(params).build_transaction({
    "from": OWNER,
    "nonce": nonce,
    "value": 0,                     # 无 ETH 附带
    "gas": 1_000_000,              # 修复：使用下划线分隔的数字
    "maxFeePerGas": w3.to_wei(30, "gwei"),
    "maxPriorityFeePerGas": w3.to_wei(1.5, "gwei"),
    "chainId": 1
})
signed  = ACCOUNT.sign_transaction(mint_tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print("Mint sent:", w3.to_hex(tx_hash))
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(receipt.values())
print("Mint confirmed in block", receipt["blockNumber"])

# 解析 logs 拿到 tokenId
logs = nfpm.events.Transfer().process_receipt(receipt)
token_id = logs[0]['args']['tokenId']
print("New position NFT tokenId =", token_id)

###############################################################################
# 5) 验证：查询 NFT 余额 + 头寸信息
###############################################################################
balance = nfpm.functions.balanceOf(OWNER).call()
pos     = nfpm.functions.positions(token_id).call()

print(f"\nNFT balance now = {balance}")
print(f"Position liquidity = {pos[7]}  (tokens_owed_0={pos[10]} , tokens_owed_1={pos[11]})")
print(f"Position tick range: [{pos[5]}, {pos[6]}]")
print(f"Position tokens: {pos[2]} (token0), {pos[3]} (token1)")