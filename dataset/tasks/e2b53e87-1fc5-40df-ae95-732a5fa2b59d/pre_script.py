import os
from web3 import Web3
from eth_account import Account
import json
import math
import time
from pathlib import Path

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

def approve_nft(token_id, spender_address):
    """
    授权指定地址使用特定的NFT代币
    
    Args:
        token_id (int): NFT代币ID
        spender_address (str): 被授权地址
    """
    try:
        # 检查当前是否已经授权
        current_approved = npm.functions.getApproved(token_id).call()
        if current_approved.lower() == spender_address.lower():
            print(f"NFT {token_id} 已经授权给 {spender_address}")
            return
        
        # 执行授权交易
        tx = npm.functions.approve(spender_address, token_id).build_transaction({
            "from": ACCOUNT.address,
            "nonce": w3.eth.get_transaction_count(ACCOUNT.address),
            "gas": 100_000,
            "chainId": CHAIN_ID,
        })
        signed = ACCOUNT.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"approve NFT {token_id} to {spender_address} tx:", tx_hash.hex())
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ NFT {token_id} 已成功授权给 {spender_address}")
        
    except Exception as e:
        print(f"❌ 授权NFT失败: {e}")

def approve_all_nft(spender_address, approved=True):
    """
    授权或取消授权指定地址使用所有NFT代币
    
    Args:
        spender_address (str): 被授权地址
        approved (bool): True为授权，False为取消授权
    """
    try:
        # 检查当前授权状态
        is_approved = npm.functions.isApprovedForAll(ACCOUNT.address, spender_address).call()
        if is_approved == approved:
            status = "已授权" if approved else "未授权"
            print(f"地址 {spender_address} {status}使用所有NFT")
            return
        
        # 执行授权/取消授权交易
        tx = npm.functions.setApprovalForAll(spender_address, approved).build_transaction({
            "from": ACCOUNT.address,
            "nonce": w3.eth.get_transaction_count(ACCOUNT.address),
            "gas": 100_000,
            "chainId": CHAIN_ID,
        })
        signed = ACCOUNT.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        action = "approve all NFT" if approved else "revoke all NFT approval"
        print(f"{action} to {spender_address} tx:", tx_hash.hex())
        w3.eth.wait_for_transaction_receipt(tx_hash)
        
        status = "授权" if approved else "取消授权"
        print(f"✅ 已成功{status}地址 {spender_address} 使用所有NFT")
        
    except Exception as e:
        print(f"❌ 批量授权NFT失败: {e}")

###############################################################################
# Main process
###############################################################################
def main():
    # If needed, wrap ETH to WETH and swap for USDC
    from evaluate_utils.common_util import wrap_eth_to_weth, transfer_eth
    from evaluate_utils.uniswap_v3_util import swap_weth_to_usdc
    import asyncio
    wrap_eth_to_weth(10)
    swap_weth_to_usdc(2)

    approve(weth, AMOUNT_WETH)
    approve(usdc, usdc_needed)
    transfer_eth(
        "0x670C68F7fE704211cAcaDa9199Db8d52335CE165",
        1
    )
    ACCOUNT = Account.from_key(os.environ.get("REAL_PRIVATE_KEY"))


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
        "deadline": int(time.time()) + 3600
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
    
    # 存储创建的NFT token ID，用于后续授权示例
    nft_token_id = 1024366
    
    for log in receipt["logs"]:
        if log["address"].lower() == NPM.lower():
            try:
                parsed = npm.events.IncreaseLiquidity().process_log(log)
                nft_token_id = parsed["args"]["tokenId"]
                print("==> Successfully created position NFT ID:", nft_token_id)
                print("     Liquidity L:", parsed["args"]["liquidity"])
            except:
                try:
                    # Try to parse Mint event
                    parsed = npm.events.Mint().process_log(log) 
                    nft_token_id = parsed["args"]["tokenId"]
                    print("==> Successfully created position NFT ID:", nft_token_id)
                    print("     Liquidity L:", parsed["args"]["liquidity"])
                except:
                    continue
    
    # NFT授权示例（可选）
    if nft_token_id is not None:
        print("\n=== NFT 授权示例 ===")
        from dataset.constants import UNISWAP_NPM_ADDRESS_ETH
        # 示例1：授权特定NFT给某个地址（比如另一个合约地址）
        example_spender = UNISWAP_NPM_ADDRESS_ETH # 替换为实际地址
        approve_nft(nft_token_id, example_spender)
        
        # 示例2：批量授权所有NFT给某个地址
        approve_all_nft(example_spender, True)  # 授权
        # approve_all_nft(example_spender, False) # 取消授权
        
        print("💡 提示：如果需要授权NFT，请取消注释上面的示例代码并设置正确的授权地址")
    else:
        print("⚠️ 未能获取到NFT token ID，无法执行授权示例")

if __name__ == "__main__":
    main()