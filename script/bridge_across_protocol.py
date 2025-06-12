from web3 import Web3
from eth_account.signers.local import LocalAccount
from dataset.constants import (
    RPC_URL,
    PRIVATE_KEY,
    WETH_CONTRACT_ADDRESS_ETH,
    ACROSS_PROTOCOL_ADDRESS_ETH,
    WETH_CONTRACT_ADDRESS_BASE
)
from evaluate_utils.common_util import wrap_eth_to_weth
import asyncio
# 初始化 Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)

# 合约地址
WETH = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH)
WETH_BASE = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_BASE)
ACROSS = Web3.to_checksum_address(ACROSS_PROTOCOL_ADDRESS_ETH)

# WETH ABI
WETH_ABI = [
    {
        "constant": False,
        "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

# Across Protocol ABI
ACROSS_ABI = [
    {
        "inputs": [
            {"name": "depositor", "type": "address"},
            {"name": "recipient", "type": "address"}, 
            {"name": "inputToken", "type": "address"},
            {"name": "outputToken", "type": "address"},
            {"name": "inputAmount", "type": "uint256"},
            {"name": "outputAmount", "type": "uint256"},
            {"name": "destinationChainId", "type": "uint256"},
            {"name": "exclusiveRelayer", "type": "address"},
            {"name": "quoteTimestamp", "type": "uint32"},
            {"name": "fillDeadline", "type": "uint32"},
            {"name": "exclusivityParameter", "type": "uint32"},
            {"name": "message", "type": "bytes"}
        ],
        "name": "depositV3",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]

# 合约实例
weth_contract = w3.eth.contract(address=WETH, abi=WETH_ABI)
across_contract = w3.eth.contract(address=ACROSS, abi=ACROSS_ABI)
exclusive_relayer = Web3.to_checksum_address("0x699ee12a1d97437a4a1e87c71e5d882b3881e2e3")
# 参数设置
amount = Web3.to_wei(1, 'ether')  # 1 WETH
base_chain_id = 8453  # BASE链ID
recipient = account.address  # 接收地址与发送地址相同
recipient = Web3.to_checksum_address("0xf8dd5e3c87bb6d92f7a00467471f69135fc16881")
# 构建交易
# 1. 授权 Across 使用 WETH
approve_tx = weth_contract.functions.approve(
    ACROSS,
    amount
).build_transaction({
    'from': account.address,
    'gas': 100000,
    'nonce': w3.eth.get_transaction_count(account.address)
})

now = w3.eth.get_block('latest').timestamp
print(now)

# 2. 调用 Across bridge
bridge_tx = across_contract.functions.depositV3(
    account.address,
    recipient,
    WETH,
    WETH_BASE,
    amount,
    amount,
    base_chain_id,
    exclusive_relayer,
    now,
    now + 3600,
    0,
    b''
).build_transaction({
    'from': account.address,
    'gas': 3000000,
    'nonce': w3.eth.get_transaction_count(account.address) + 1
})
print(amount)
print(bridge_tx)
# 签名并发送交易
signed_approve_tx = account.sign_transaction(approve_tx)
signed_bridge_tx = account.sign_transaction(bridge_tx)

# 发送交易
tx_hash1 = w3.eth.send_raw_transaction(signed_approve_tx.raw_transaction)
tx_hash2 = w3.eth.send_raw_transaction(signed_bridge_tx.raw_transaction)

# 等待交易确认并打印收据
print("等待交易确认...")
receipt1 = w3.eth.wait_for_transaction_receipt(tx_hash1)
receipt2 = w3.eth.wait_for_transaction_receipt(tx_hash2)

print("\n授权交易收据:")
print(f"交易哈希: {receipt1['transactionHash'].hex()}")
print(f"状态: {'成功' if receipt1['status'] == 1 else '失败'}")
print(f"使用的gas: {receipt1['gasUsed']}")
print(f"区块号: {receipt1['blockNumber']}")

print("\n跨链桥交易收据:")
print(f"交易哈希: {receipt2['transactionHash'].hex()}")
print(f"状态: {'成功' if receipt2['status'] == 1 else '失败'}")
print(f"使用的gas: {receipt2['gasUsed']}")
print(f"区块号: {receipt2['blockNumber']}")
print(receipt2.values())
