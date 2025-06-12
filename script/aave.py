
import json
from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import USDT_CONTRACT_ADDRESS_ETH, AAVE_POOL_ADDRESS_ETH, RPC_URL, PRIVATE_KEY, WETH_CONTRACT_ADDRESS_ETH

# 初始化 web3
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

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
# AAVE V3 Pool ABI
AAVE_POOL_ABI = [
    {
        "inputs": [
            {"name": "asset", "type": "address"},
            {"name": "amount", "type": "uint256"},
            {"name": "interestRateMode", "type": "uint256"},
            {"name": "referralCode", "type": "uint16"},
            {"name": "onBehalfOf", "type": "address"}
        ],
        "name": "borrow",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]
AAVE_POOL_ABI.append({
    "inputs": [
        {"name": "asset", "type": "address"},
        {"name": "amount", "type": "uint256"},
        {"name": "onBehalfOf", "type": "address"},
        {"name": "referralCode", "type": "uint16"}
    ],
    "name": "supply",
    "outputs": [],
    "stateMutability": "nonpayable", 
    "type": "function"
})

# 初始化合约
USDT = Web3.to_checksum_address(USDT_CONTRACT_ADDRESS_ETH)
AAVE_POOL = Web3.to_checksum_address(AAVE_POOL_ADDRESS_ETH)
aave_pool = w3.eth.contract(address=AAVE_POOL, abi=AAVE_POOL_ABI)

async def borrow_usdt():
    # 构建借款交易
    amount = 10 * 10**6  # 10 USDT (6位小数)
    
    tx = aave_pool.functions.borrow(
        USDT,           # 借款资产
        amount,         # 借款金额
        2,             # 利率模式 (2=变动利率)
        0,             # 推荐码
        addr           # 借款人
    ).build_transaction({
        'from': addr,
        'gas': 500000,
        'nonce': w3.eth.get_transaction_count(addr),
    })
    
    # 签名并发送交易
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    # 等待交易确认
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return f"借款交易已确认: {receipt.transactionHash.hex()}"

# 增加AAVE Pool ABI中的supply方法

# 初始化WETH合约地址
WETH = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH)

async def supply_eth():
    # 构建存款交易
    amount = Web3.to_wei(1, 'ether')  # 1 ETH

    # 先把ETH转换为WETH
    weth_contract = w3.eth.contract(address=WETH, abi=WETH_ABI)
    deposit_tx = weth_contract.functions.deposit().build_transaction({
        'from': addr,
        'value': amount,
        'gas': 100000,
        'nonce': w3.eth.get_transaction_count(addr)
    })
    
    # 签名并发送交易
    signed_deposit = account.sign_transaction(deposit_tx)
    deposit_hash = w3.eth.send_raw_transaction(signed_deposit.raw_transaction)

    w3.eth.wait_for_transaction_receipt(deposit_hash)
    print(f"已将 {Web3.from_wei(amount,'ether')} ETH 转换为 WETH")
    
    # 授权Aave Pool合约使用WETH
    approve_tx = weth_contract.functions.approve(AAVE_POOL, amount*2).build_transaction({
        'from': addr,
        'gas': 100000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': w3.eth.get_transaction_count(addr)
    })
    
    # 签名并发送授权交易
    signed_approve = account.sign_transaction(approve_tx)
    approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
    w3.eth.wait_for_transaction_receipt(approve_hash)
    print("已授权 Aave Pool 使用 WETH")
    
    tx = aave_pool.functions.supply(
        WETH,          # 存入资产(ETH需要先转换为WETH)
        amount,        # 存入金额
        addr,          # 受益人
        0             # 推荐码
    ).build_transaction({
        'from': addr,
        "value": 0,
        'gas': 5000000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': w3.eth.get_transaction_count(addr),
    })
    
    # 签名并发送交易
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    # 等待交易确认
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return f"存入ETH交易已确认: {receipt.values()}"


if __name__ == '__main__':
    import asyncio
    print(asyncio.run(borrow_usdt()))
