from web3 import Web3
from eth_account import Account
import json
import math
from pathlib import Path

###############################################################################
# 环境参数 – 请根据自己情况修改
###############################################################################
RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
ACCOUNT = Account.from_key(PRIVATE_KEY)
CHAIN_ID = 1                                                # mainnet=1, sepolia=11155111…

###############################################################################
# 合约常量
###############################################################################
WETH  = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0E5C4F27eAD9083C756Cc2")
USDC  = Web3.to_checksum_address("0xA0b86991C6218b36c1d19D4a2e9Eb0cE3606EB48")
POOL  = Web3.to_checksum_address("0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640") # WETH/USDC 0.05 %
NPM   = Web3.to_checksum_address("0xC36442b4a4522E871399CD717aBDD847Ab11FE88") # NonfungiblePositionManager

AMOUNT_WETH = Web3.to_wei(2, "ether")           # 想投入的 WETH 数量
PRICE_BAND  = 0.01                              # tick ±1 % 宽度

###############################################################################
# 加载 ABI（只用到的函数片段，减小脚本体积）
###############################################################################
script_dir = Path(__file__).parent
abi_dir = script_dir.parent.parent.parent / "abi"
with open(abi_dir / "uniswap_v3_pool_abi.json") as f:
    POOL_ABI = json.load(f)
with open(abi_dir / "uniswap_v3_npm_abi.json") as f:
    NPM_ABI = json.load(f)
with open(abi_dir / "erc20_abi.json") as f:
    ERC20_ABI = json.load(f)

###############################################################################
# 工具：Tick ↔ Price 互转
###############################################################################
def price_to_tick(price):
    return int(math.log(price, 1.0001))

def nearest_tick(tick, spacing=10):
    return tick - (tick % spacing)

###############################################################################
# 连接链并实例化合约
###############################################################################
w3 = Web3(Web3.HTTPProvider(RPC_URL))
pool = w3.eth.contract(address=POOL, abi=POOL_ABI)
npm  = w3.eth.contract(address=NPM,  abi=NPM_ABI)
weth = w3.eth.contract(address=WETH, abi=ERC20_ABI)
usdc = w3.eth.contract(address=USDC, abi=ERC20_ABI)

###############################################################################
# 1) 若手里是原生 ETH 而非 WETH – 先 wrap
###############################################################################

###############################################################################
# 2) 读取池价格，估算需要配对的 USDC
###############################################################################
slot0 = pool.functions.slot0().call()
sqrtPriceX96 = slot0[0]

# 正确计算价格 - 考虑token0和token1的顺序
# 在USDC/WETH池中，USDC是token0，WETH是token1
# sqrtPriceX96 = sqrt(token1/token0) * 2^96
# 所以 price = (sqrtPriceX96/2^96)^2 = token1/token0 = WETH/USDC
weth_per_usdc = (sqrtPriceX96 / (2**96)) ** 2

# 我们需要 USDC/WETH 的比率
usdc_per_weth = 1 / weth_per_usdc

# 计算需要的USDC数量（考虑小数位差异）
# AMOUNT_WETH 是18位小数的wei
# USDC是6位小数
# usdc_per_weth是token单位比率，需要调整到wei单位
usdc_needed = int(AMOUNT_WETH * usdc_per_weth)

print(f"Pool price ≈ {usdc_per_weth*1e12:,.2f} USDC/WETH")
print(f"需要约 {usdc_needed / 10**6:,.2f} USDC ({usdc_needed} wei)")

###############################################################################
# 3) 计算 tick 区间
###############################################################################
def align_to_spacing(tick, spacing):
    return tick - (tick % spacing)
current_tick = slot0[1]
tick_spacing=10
band_ticks   = int(math.log(1+PRICE_BAND, 1.0001))        # ≈96
lower_tick   = align_to_spacing(current_tick - band_ticks, tick_spacing)
upper_tick   = align_to_spacing(current_tick + band_ticks, tick_spacing)
print("tick range:", lower_tick, "→", upper_tick)

###############################################################################
# 4) 批准 WETH & USDC 给 NPM
###############################################################################
def approve(token, amount):
    allowance = token.functions.allowance(ACCOUNT.address, NPM).call()
    if allowance < amount:
        tx = token.functions.approve(NPM, 2**256-1).build_transaction({
            "from": ACCOUNT.address,
            "nonce": w3.eth.get_transaction_count(ACCOUNT.address),
            "gas": 80_000,
            "chainId": CHAIN_ID,
        })
        signed = ACCOUNT.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"approve {token.functions.symbol().call()} tx:", tx_hash.hex())
        w3.eth.wait_for_transaction_receipt(tx_hash)

###############################################################################
# 主流程
###############################################################################
def main():
    # 若需要，先 wrap
    from evaluate_utils.common_util import wrap_eth_to_weth
    from evaluate_utils.uniswap_v3_util import swap_weth_to_usdc
    import asyncio
    asyncio.run(wrap_eth_to_weth(10))
    asyncio.run(swap_weth_to_usdc(2))

    approve(weth, AMOUNT_WETH)
    approve(usdc, usdc_needed)

    # 放宽滑点保护，使用90%而非95%
    params = {
        "token0": USDC,
        "token1": WETH,
        "fee": 500,                           # 0.05 %
        "tickLower": lower_tick,
        "tickUpper": upper_tick,
        "amount0Desired": usdc_needed,        # USDC (6 dec)
        "amount1Desired": AMOUNT_WETH,        # WETH (18 dec)
        "amount0Min": int(usdc_needed * 0.80),  # 放宽滑点到10%
        "amount1Min": int(AMOUNT_WETH * 0.80),  # 放宽滑点到10%
        "recipient": ACCOUNT.address,
        "deadline": w3.eth.get_block("latest")["timestamp"] + 3600
    }

    # 增加gas限制，防止out of gas
    tx = npm.functions.mint(params).build_transaction({
        "from": ACCOUNT.address,
        "nonce": w3.eth.get_transaction_count(ACCOUNT.address),
        "gas": 1_000_000,  # 增加gas限制
        "chainId": CHAIN_ID,
    })
    signed = ACCOUNT.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print("mint liquidity tx:", tx_hash.hex())

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("Transaction successful!")
    for log in receipt["logs"]:
        if log["address"].lower() == NPM.lower():
            try:
                parsed = npm.events.IncreaseLiquidity().process_log(log)
                print("==> 成功创建头寸 NFT ID:", parsed["args"]["tokenId"])
                print("     流动性 L:", parsed["args"]["liquidity"])
            except:
                try:
                    # 尝试解析Mint事件
                    parsed = npm.events.Mint().process_log(log) 
                    print("==> 成功创建头寸 NFT ID:", parsed["args"]["tokenId"])
                    print("     流动性 L:", parsed["args"]["liquidity"])
                except:
                    continue

if __name__ == "__main__":
    main()