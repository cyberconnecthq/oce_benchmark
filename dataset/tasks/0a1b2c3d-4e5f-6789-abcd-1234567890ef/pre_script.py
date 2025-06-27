from web3 import Web3
from eth_account import Account
import json
import math
from pathlib import Path
import time

###############################################################################
# Environment parameters – please modify according to your setup
###############################################################################
RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
ACCOUNT = Account.from_key(PRIVATE_KEY)
CHAIN_ID = 1  # mainnet=1, sepolia=11155111, etc.

###############################################################################
# Contract constants
###############################################################################
WETH  = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0E5C4F27eAD9083C756Cc2")
USDC  = Web3.to_checksum_address("0xA0b86991C6218b36c1d19D4a2e9Eb0cE3606EB48")
POOL  = Web3.to_checksum_address("0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640") # WETH/USDC 0.05 %
NPM   = Web3.to_checksum_address("0xC36442b4a4522E871399CD717aBDD847Ab11FE88") # NonfungiblePositionManager

AMOUNT_WETH = Web3.to_wei(2, "ether")           # Amount of WETH to provide
PRICE_BAND  = 0.01                              # tick ±1 % width

###############################################################################
# Load ABIs (only necessary fragments to reduce script size)
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
# Utility: Tick ↔ Price conversion
###############################################################################
def price_to_tick(price):
    return int(math.log(price, 1.0001))

def nearest_tick(tick, spacing=10):
    return tick - (tick % spacing)

###############################################################################
# Connect to chain and instantiate contracts
###############################################################################
w3 = Web3(Web3.HTTPProvider(RPC_URL))
pool = w3.eth.contract(address=POOL, abi=POOL_ABI)
npm  = w3.eth.contract(address=NPM,  abi=NPM_ABI)
weth = w3.eth.contract(address=WETH, abi=ERC20_ABI)
usdc = w3.eth.contract(address=USDC, abi=ERC20_ABI)

###############################################################################
# 1) If you have native ETH instead of WETH – wrap first
###############################################################################

###############################################################################
# 2) Read pool price and estimate required USDC
###############################################################################
slot0 = pool.functions.slot0().call()
sqrtPriceX96 = slot0[0]

# Correct price calculation - consider token0 and token1 order
# In the USDC/WETH pool, USDC is token0, WETH is token1
# sqrtPriceX96 = sqrt(token1/token0) * 2^96
# So price = (sqrtPriceX96/2^96)^2 = token1/token0 = WETH/USDC
weth_per_usdc = (sqrtPriceX96 / (2**96)) ** 2

# We need the USDC/WETH ratio
usdc_per_weth = 1 / weth_per_usdc

# Calculate required USDC amount (considering decimal differences)
# AMOUNT_WETH is in wei (18 decimals)
# USDC uses 6 decimals
# usdc_per_weth is in token units, need to adjust to wei units
usdc_needed = int(AMOUNT_WETH * usdc_per_weth)

print(f"Pool price ≈ {usdc_per_weth*1e12:,.2f} USDC/WETH")
print(f"Need about {usdc_needed / 10**6:,.2f} USDC ({usdc_needed} wei)")

###############################################################################
# 3) Calculate tick range
###############################################################################
def align_to_spacing(tick, spacing):
    return tick - (tick % spacing)
current_tick = slot0[1]
tick_spacing = 10
band_ticks   = int(math.log(1+PRICE_BAND, 1.0001))        # ≈96
lower_tick   = align_to_spacing(current_tick - band_ticks, tick_spacing)
upper_tick   = align_to_spacing(current_tick + band_ticks, tick_spacing)
print("tick range:", lower_tick, "→", upper_tick)

###############################################################################
# 4) Approve WETH & USDC to NPM
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
# 创建同步版本的swap函数
###############################################################################
def swap_weth_to_usdc_sync(amount_weth: float):
    """
    同步版本：使用Uniswap V3将WETH换成USDC
    
    Args:
        amount_weth: 要交换的WETH数量
    """
    amount_in_wei = int(amount_weth * 10**18)
    
    # Router地址
    ROUTER = Web3.to_checksum_address("0xE592427A0AEce92De3Edee1F18E0157C05861564")
    
    # 1. Approve Router
    print("\nApproving Router to spend WETH...")
    approve(weth, amount_in_wei)

    # 2. Swap WETH to USDC
    router_abi = [{"inputs":[{"components":[
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
    "stateMutability":"payable","type":"function"}]
    
    router = w3.eth.contract(address=ROUTER, abi=router_abi)
    deadline = int(w3.eth.get_block("latest").get("timestamp", int(time.time()))) + 600
    params = (
        WETH,
        USDC,
        500,  # 0.05% fee tier
        ACCOUNT.address,
        deadline,
        amount_in_wei,
        0,  # amountOutMinimum
        0   # sqrtPriceLimitX96
    )

    print("Executing swap...")
    tx = router.functions.exactInputSingle(params).build_transaction({
        "from": ACCOUNT.address,
        "value": 0,
        "gas": 300_000,
        "nonce": w3.eth.get_transaction_count(ACCOUNT.address),
        "chainId": CHAIN_ID,
    })
    signed = ACCOUNT.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("Swap complete, gas used:", receipt["gasUsed"])

###############################################################################
# Main process
###############################################################################
def main():
    # If needed, wrap ETH to WETH and swap for USDC
    from evaluate_utils.common_util import wrap_eth_to_weth
    
    # 使用同步调用
    wrap_eth_to_weth(10)
    swap_weth_to_usdc_sync(2)

    approve(weth, AMOUNT_WETH)
    approve(usdc, usdc_needed)

    # Loosen slippage protection, use 80% instead of 95%
    params = {
        "token0": USDC,
        "token1": WETH,
        "fee": 500,                           # 0.05 %
        "tickLower": lower_tick,
        "tickUpper": upper_tick,
        "amount0Desired": usdc_needed,        # USDC (6 dec)
        "amount1Desired": AMOUNT_WETH,        # WETH (18 dec)
        "amount0Min": int(usdc_needed * 0.80),  # Loosen slippage to 20%
        "amount1Min": int(AMOUNT_WETH * 0.80),  # Loosen slippage to 20%
        "recipient": ACCOUNT.address,
        "deadline": int(w3.eth.get_block("latest").get("timestamp", int(time.time()))) + 3600
    }

    # Increase gas limit to prevent out of gas
    tx = npm.functions.mint(params).build_transaction({
        "from": ACCOUNT.address,
        "nonce": w3.eth.get_transaction_count(ACCOUNT.address),
        "gas": 1_000_000,  # Increased gas limit
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
                print("==> Successfully created position NFT ID:", parsed["args"]["tokenId"])
                print("     Liquidity L:", parsed["args"]["liquidity"])
            except:
                try:
                    # Try to parse Mint event
                    parsed = npm.events.Mint().process_log(log) 
                    print("==> Successfully created position NFT ID:", parsed["args"]["tokenId"])
                    print("     Liquidity L:", parsed["args"]["liquidity"])
                except:
                    continue

if __name__ == "__main__":
    main()