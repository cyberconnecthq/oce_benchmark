from web3 import Web3
from eth_account import Account
import json
from pathlib import Path

# Environment variables
RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
ACCOUNT = Account.from_key(PRIVATE_KEY)
CHAIN_ID = 1

# Contract addresses
USDC = Web3.to_checksum_address("0xA0b86991C6218b36c1d19D4a2e9Eb0cE3606EB48")
SPENDER_A = Web3.to_checksum_address("0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA") # Address A

# Load ABI
script_dir = Path(__file__).parent
abi_dir = script_dir.parent / "abi"
with open(abi_dir / "erc20_abi.json") as f:
    ERC20_ABI = json.load(f)

# Connect to chain and instantiate contract
w3 = Web3(Web3.HTTPProvider(RPC_URL))
usdc = w3.eth.contract(address=USDC, abi=ERC20_ABI)

def main():
    # Approve 10 USDC (6 decimals)
    amount = 10 * 10**6
    
    tx = usdc.functions.approve(SPENDER_A, amount).build_transaction({
        "from": ACCOUNT.address,
        "nonce": w3.eth.get_transaction_count(ACCOUNT.address),
        "gas": 80_000,
        "chainId": CHAIN_ID,
    })
    
    signed = ACCOUNT.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"USDC approval tx hash: {tx_hash.hex()}")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(receipt.values())
    print("Approval transaction successful!")

if __name__ == "__main__":
    approve_usdc()
