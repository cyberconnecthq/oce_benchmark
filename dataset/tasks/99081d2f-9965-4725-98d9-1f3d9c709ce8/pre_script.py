#!/usr/bin/env python3
"""
swap_eth_to_pepe.py (Uniswap V2 version)

Process:
1) Directly swap ETH to PEPE using Uniswap V2
2) Print balance and price info before and after swap
"""

import os, time, json
from decimal import Decimal
from web3 import Web3, HTTPProvider
from web3.types import (
    TxParams,
)
from eth_account.signers.local import (
    LocalAccount,
)
from evaluate_utils.common_util import wrap_eth_to_weth
import asyncio
def main():
    wrap_eth_to_weth(1)
    # ─── Basic Config ────────────────────────────────────────────────────────────────
    RPC_URL =  "http://127.0.0.1:8545"
    PRIVATE_KEY = os.getenv(
        "PRIV_KEY",
        # Default first Anvil account
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    )
    AMOUNT_IN_ETH = Decimal("0.1")      # Amount of ETH to swap

    # Contract Addresses (Uniswap V2)
    WETH  = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0E5C4F27eAD9083C756Cc2")
    PEPE  = Web3.to_checksum_address("0x6982508145454Ce325dDbE47a25d4ec3d2311933")  # PEPE token address
    ROUTER_V2 = Web3.to_checksum_address("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")  # Uniswap V2 Router

    w3 = Web3(HTTPProvider(RPC_URL))
    account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
    addr = account.address
    print(f"Connected to {RPC_URL}, use account {addr}")

    # ─── ERC20 ABI ────────────────────────────────────────────────────────────────
    ERC20_ABI = json.loads("""[
    {"constant":true,"inputs":[{"name":"owner","type":"address"}],
    "name":"balanceOf","outputs":[{"name":"","type":"uint256"}],
    "stateMutability":"view","type":"function"},
    {"constant":true,"inputs":[],
    "name":"decimals","outputs":[{"name":"","type":"uint8"}],
    "stateMutability":"view","type":"function"},
    {"constant":true,"inputs":[],
    "name":"symbol","outputs":[{"name":"","type":"string"}],
    "stateMutability":"view","type":"function"}
    ]""")

    # ─── Uniswap V2 Router ABI ────────────────────────────────────────────────────
    ROUTER_V2_ABI = json.loads("""[
    {"name":"getAmountsOut","type":"function","stateMutability":"view",
    "inputs":[{"name":"amountIn","type":"uint256"},
                {"name":"path","type":"address[]"}],
    "outputs":[{"name":"","type":"uint256[]"}]},
    {"name":"swapExactETHForTokens","type":"function","stateMutability":"payable",
    "inputs":[{"name":"amountOutMin","type":"uint256"},
                {"name":"path","type":"address[]"},
                {"name":"to","type":"address"},
                {"name":"deadline","type":"uint256"}],
    "outputs":[{"name":"","type":"uint256[]"}]},
    {"name":"WETH","type":"function","stateMutability":"view",
    "inputs":[],
    "outputs":[{"name":"","type":"address"}]}
    ]""")

    # Initialize contracts
    pepe_contract = w3.eth.contract(address=PEPE, abi=ERC20_ABI)
    router_v2 = w3.eth.contract(address=ROUTER_V2, abi=ROUTER_V2_ABI)

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

    def get_pepe_decimals():
        """Get PEPE token decimals"""
        try:
            return pepe_contract.functions.decimals().call()
        except:
            return 18  # Default value

    def get_current_price():
        """Get current ETH/PEPE price"""
        try:
            amount_in = 10**18  # 1 ETH
            path = [WETH, PEPE]
            
            amounts_out = router_v2.functions.getAmountsOut(amount_in, path).call()
            pepe_out = amounts_out[1]
            pepe_decimals = get_pepe_decimals()
            
            pepe_per_eth = fmt(pepe_out, pepe_decimals)
            print(f"Current price: 1 ETH = {pepe_per_eth:,.0f} PEPE")
            return pepe_per_eth
        except Exception as e:
            print(f"Failed to get price: {e}")
            return Decimal("0")

    def get_balance_info():
        """Get balance information"""
        eth_balance = w3.eth.get_balance(addr)
        pepe_balance = pepe_contract.functions.balanceOf(addr).call()
        pepe_decimals = get_pepe_decimals()
        
        print(f"ETH balance: {fmt(eth_balance):,.4f} ETH")
        print(f"PEPE balance: {fmt(pepe_balance, pepe_decimals):,.0f} PEPE")
        return eth_balance, pepe_balance

    # ─── Show Initial State ────────────────────────────────────────────────────────────
    print("\n📊 Initial state:")
    get_balance_info()
    current_price = get_current_price()

    # ─── Calculate Expected Output ────────────────────────────────────────────────────
    amount_in_wei = int(AMOUNT_IN_ETH * 10**18)
    path = [WETH, PEPE]

    try:
        amounts_out = router_v2.functions.getAmountsOut(amount_in_wei, path).call()
        expected_pepe = amounts_out[1]
        pepe_decimals = get_pepe_decimals()
        
        print(f"\n💰 Expected output for {AMOUNT_IN_ETH} ETH:")
        print(f"   {fmt(expected_pepe, pepe_decimals):,.0f} PEPE")
        
        # Set minimum output amount (95% of expected output, 5% slippage)
        min_amount_out = int(expected_pepe * 0.95)
        
    except Exception as e:
        print(f"Failed to get expected output: {e}")
        min_amount_out = 1  # Set minimum value

    # ─── Execute Swap ────────────────────────────────────────────────────────────────
    print(f"\n🔄 Starting Swap: {AMOUNT_IN_ETH} ETH → PEPE")

    deadline = int(time.time()) + 600  # Expires in 10 minutes

    try:
        swap_tx = router_v2.functions.swapExactETHForTokens(
            min_amount_out,  # amountOutMin
            path,           # path [WETH, PEPE]
            addr,           # to
            deadline        # deadline
        ).build_transaction({
            "from": addr,
            "value": amount_in_wei,
            "gas": 300_000
        })
        print(swap_tx)
        print("Sending transaction...")
        receipt = send(swap_tx)
        print(f"✅ Swap successful! Gas used: {receipt.gasUsed:,}")
        print(f"Transaction hash: {receipt.transactionHash.hex()}")
        
    except Exception as e:
        print(f"❌ Swap failed: {e}")
        exit(1)

    # ─── Show Final Results ────────────────────────────────────────────────────────────
    print("\n📊 State after swap:")
    final_eth_balance, final_pepe_balance = get_balance_info()

    # Calculate actual PEPE received
    pepe_decimals = get_pepe_decimals()
    pepe_received = fmt(final_pepe_balance, pepe_decimals)

    print(f"\n🎉 Transaction Summary:")
    print(f"   Spent: {AMOUNT_IN_ETH} ETH")
    print(f"   Received: {pepe_received:,.0f} PEPE")

    if current_price > 0:
        actual_rate = pepe_received / AMOUNT_IN_ETH
        price_impact = ((current_price - actual_rate) / current_price) * 100
        print(f"   Actual rate: 1 ETH = {actual_rate:,.0f} PEPE")
        print(f"   Price impact: {price_impact:.2f}%")

    print("\n✨ PEPE swap completed!")