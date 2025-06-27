import json
from eth_typing import ChecksumAddress
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

AAVE_POOL_ABI = [
    {
        "inputs": [{"name": "user", "type": "address"}],
        "name": "getUserAccountData",
        "outputs": [
            {"name": "totalCollateralBase", "type": "uint256"},
            {"name": "totalDebtBase", "type": "uint256"},
            {"name": "availableBorrowsBase", "type": "uint256"},
            {"name": "currentLiquidationThreshold", "type": "uint256"},
            {"name": "ltv", "type": "uint256"},
            {"name": "healthFactor", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
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
    },
    {
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
    }
]

# 初始化合约
USDT = Web3.to_checksum_address(USDT_CONTRACT_ADDRESS_ETH)
WETH = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH)
AAVE_POOL = Web3.to_checksum_address(AAVE_POOL_ADDRESS_ETH)
aave_pool = w3.eth.contract(address=AAVE_POOL, abi=AAVE_POOL_ABI)

async def get_aave_info(address: ChecksumAddress|str):
    if isinstance(address, str):
        address = Web3.to_checksum_address(address)
    (total_collateral, total_debt, available_borrows, _, _, health_factor) = aave_pool.functions.getUserAccountData(address).call()
    return (
        f"Aave Lending Status of address {address}:\n"
        f"Total Collateral: {total_collateral / 10**8} USD\n"
        f"Total Debt: {total_debt / 10**8} USD\n"
        f"Available Borrow: {available_borrows / 10**8} USD\n"
        f"Health Factor: {health_factor / 10**18}\n"
    )

def borrow_usdt(amount_usdt: float):
    # 构建借款交易
    amount = int(amount_usdt * 10**6)  # USDT 6位小数
    
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

def supply_eth(amount_eth: float):
    # 构建存款交易
    amount = Web3.to_wei(amount_eth, 'ether')

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
    print(f"已将 {amount_eth} ETH 转换为 WETH")
    
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

async def supply_aave_v3_token(token_add, address, amount):
    """
    向Aave V3存入任意ERC20代币
    :param token_add: 代币合约地址 (str)
    :param address: 存款人地址 (str)
    :param amount: 存款数量 (int, 单位为最小单位)
    :return: 交易哈希
    """
    # 初始化合约
    token_add = Web3.to_checksum_address(token_add)
    token_contract = w3.eth.contract(address=token_add, abi=ERC20_ABI)
    # 授权Aave Pool合约
    approve_tx = token_contract.functions.approve(AAVE_POOL, amount).build_transaction({
        'from': address,
        'gas': 100000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': w3.eth.get_transaction_count(address)
    })
    signed_approve = account.sign_transaction(approve_tx)
    approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
    w3.eth.wait_for_transaction_receipt(approve_hash)
    print(f"已授权Aave Pool使用 {amount} token: {token_add}")

    # 调用Aave Pool的supply方法
    tx = aave_pool.functions.supply(
        token_add,
        amount,
        address,
        0
    ).build_transaction({
        'from': address,
        'value': 0,
        'gas': 500000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': w3.eth.get_transaction_count(address)
    })
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"存入Aave V3成功, 交易哈希: {receipt.transactionHash.hex()}")
    return receipt.values()




if __name__ == '__main__':
    import asyncio
    # print(asyncio.run(get_aave_info("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")))
    from dataset.constants import USDT_CONTRACT_ADDRESS_ETH
    print(asyncio.run(supply_aave_v3_token(USDT_CONTRACT_ADDRESS_ETH, addr, 1000*10**6)))