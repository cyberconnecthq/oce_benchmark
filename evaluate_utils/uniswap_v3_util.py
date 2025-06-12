
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

# Uniswap V3合约地址
ROUTER = Web3.to_checksum_address("0xE592427A0AEce92De3Edee1F18E0157C05861564")
QUOTER = Web3.to_checksum_address("0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6")

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

async def swap_weth_to_usdc(amount_weth: float):
    """
    使用Uniswap V3将ETH换成USDC
    
    Args:
        amount_weth: 要交换的WETH数量
    """
    amount_in_wei = int(amount_weth * 10**18)
    
    # 1. Wrap ETH to WETH
    weth = w3.eth.contract(address=Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH), abi=WETH_ABI)

    # 2. Approve Router
    print("\n2. Approving Router to spend WETH...")
    receipt = send_transaction(
        weth.functions.approve(ROUTER, amount_in_wei).build_transaction({
            "from": addr,
            "gas": 80_000
        })
    )
    print("   Approval complete")

    # 3. Swap WETH to USDC
    router = w3.eth.contract(address=ROUTER, abi=ROUTER_ABI)
    deadline = int(time.time()) + 600
    params = (
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),
        Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH),
        500,  # 0.05% fee tier
        addr,
        deadline,
        amount_in_wei,
        0,  # amountOutMinimum
        0   # sqrtPriceLimitX96
    )

    print("\n3. Executing swap...")
    receipt = send_transaction(
        router.functions.exactInputSingle(params).build_transaction({
            "from": addr,
            "value": 0,
            "gas": 300_000
        })
    )
    print("Swap complete, gas used:", receipt.gasUsed)

    # 检查USDC余额
    usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH), abi=ERC20_ABI)
    usdc_balance = usdc.functions.balanceOf(addr).call()
    print(f"\nSwap结果: 获得 {usdc_balance / 10**6:.2f} USDC")
