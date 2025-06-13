import os, time, json
from decimal import Decimal
from web3 import Web3, HTTPProvider
from web3.types import TxParams
from eth_account.signers.local import LocalAccount
from dataset.constants import (
    RPC_URL, PRIVATE_KEY,
    WETH_CONTRACT_ADDRESS_ETH,
    USDC_CONTRACT_ADDRESS_ETH
)
from dataset.constants import UNISWAP_V4_ROUTER_ADDRESS_ETH, UNISWAP_V4_QUETOR_ADDRESS_ETH
# Uniswap V4合约地址
ROUTER = Web3.to_checksum_address(UNISWAP_V4_ROUTER_ADDRESS_ETH)
QUOTER = Web3.to_checksum_address(UNISWAP_V4_QUETOR_ADDRESS_ETH)

# 最小ABI
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
]""") + ERC20_ABI

ROUTER_ABI = json.loads("""[
  {"inputs":[{"internalType":"bytes","name":"commands","type":"bytes"},{"internalType":"bytes[]","name":"inputs","type":"bytes[]"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"execute","outputs":[],"stateMutability":"payable","type":"function"}""")

w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

def send_transaction(tx: TxParams):
    tx.update({
        "nonce": w3.eth.get_transaction_count(addr),
        "chainId": w3.eth.chain_id,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

async def swap_eth_to_usdc(amount_eth: float):
    """
    使用Uniswap V4将ETH换成USDC
    
    Args:
        amount_eth: 要交换的ETH数量
    """
    amount_in_wei = int(amount_eth * 10**18)
    
    # 1. Approve Router
    print("\n1. Approving Router to spend ETH...")
    weth = w3.eth.contract(address=Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH), abi=WETH_ABI)
    receipt = send_transaction(
        weth.functions.approve(ROUTER, amount_in_wei).build_transaction({
            "from": addr,
            "gas": 80_000
        })
    )
    print("   Approval complete")

    # 2. Swap ETH to USDC
    router = w3.eth.contract(address=ROUTER, abi=ROUTER_ABI)
    deadline = int(time.time()) + 600
    commands = b'\x00'  # SWAP command
    inputs = [
        Web3.to_bytes(hexstr='0x12345678')  # Placeholder swap params, need actual encoding
    ]

    print("\n2. Executing swap...")
    receipt = send_transaction(
        router.functions.execute(
            commands,
            inputs,
            deadline
        ).build_transaction({
            "from": addr,
            "value": amount_in_wei,
            "gas": 300_000
        })
    )
    print("Swap complete, gas used:", receipt.gasUsed)

    # 检查USDC余额
    usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH), abi=ERC20_ABI)
    usdc_balance = usdc.functions.balanceOf(addr).call()
    print(f"\nSwap结果: 获得 {usdc_balance / 10**6:.2f} USDC")


if __name__ == "__main__":
    import asyncio
    asyncio.run(swap_eth_to_usdc(1))