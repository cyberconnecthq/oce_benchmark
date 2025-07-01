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
    return f"借款交易已确认: {receipt['transactionHash'].hex()}"

def borrow_token(token_address: str, amount: float, decimals: int = 18, interest_rate_mode: int = 2, referral_code: int = 0):
    """
    向Aave V3借出任意ERC20代币
    
    Args:
        token_address (str): 代币合约地址
        amount (float): 借款数量（以代币单位表示）
        decimals (int): 代币小数位数（默认18位）
        interest_rate_mode (int): 利率模式（1=稳定利率，2=变动利率，默认2）
        referral_code (int): 推荐码（默认0）
    
    Returns:
        str: 交易哈希或错误信息
    """
    try:
        print("=== Aave V3 Borrow Token Transaction ===")
        print(f"借款代币地址: {token_address}")
        print(f"借款数量: {amount} tokens")
        print(f"代币小数位数: {decimals}")
        print(f"利率模式: {'稳定利率' if interest_rate_mode == 1 else '变动利率'}")
        
        # 确保地址格式正确
        token_address = Web3.to_checksum_address(token_address)
        
        # 转换为最小单位
        amount_wei = int(amount * 10**decimals)
        
        # 检查用户账户状态
        (total_collateral, total_debt, available_borrows, _, _, health_factor) = aave_pool.functions.getUserAccountData(addr).call()
        
        print(f"账户状态:")
        print(f"  总抵押品价值: ${total_collateral / 10**8:.2f}")
        print(f"  总债务: ${total_debt / 10**8:.2f}")
        print(f"  可借款额度: ${available_borrows / 10**8:.2f}")
        print(f"  健康因子: {health_factor / 10**18:.2f}")
        
        # 检查是否有足够的抵押品
        if total_collateral == 0:
            return "❌ 错误：您没有抵押品，无法借款。请先存入抵押品。"
        
        if available_borrows == 0:
            return "❌ 错误：您的可借款额度为0。请检查抵押品数量或偿还部分债务。"
        
        # 构建借款交易
        tx = aave_pool.functions.borrow(
            token_address,     # 借款资产地址
            amount_wei,        # 借款金额（最小单位）
            interest_rate_mode, # 利率模式
            referral_code,     # 推荐码
            addr              # 借款人地址
        ).build_transaction({
            'from': addr,
            'gas': 500000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': w3.eth.get_transaction_count(addr),
        })
        
        print(f"交易详情: {tx}")
        
        # 签名并发送交易
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"交易已发送，哈希: {tx_hash.hex()}")
        
        # 等待交易确认
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt['status'] == 1:
            # 检查借款后的账户状态
            (new_total_collateral, new_total_debt, new_available_borrows, _, _, new_health_factor) = aave_pool.functions.getUserAccountData(addr).call()
            
            print(f"✅ 借款成功！")
            print(f"   借款数量: {amount} tokens")
            print(f"   代币地址: {token_address}")
            print(f"   交易哈希: {tx_hash.hex()}")
            print(f"   Gas使用量: {receipt['gasUsed']}")
            print(f"   区块号: {receipt['blockNumber']}")
            print(f"更新后的账户状态:")
            print(f"   总债务: ${new_total_debt / 10**8:.2f} (增加 ${(new_total_debt - total_debt) / 10**8:.2f})")
            print(f"   剩余可借: ${new_available_borrows / 10**8:.2f}")
            print(f"   健康因子: {new_health_factor / 10**18:.2f}")
            
            if new_health_factor / 10**18 < 1.5:
                print("⚠️  警告：您的健康因子较低，有清算风险！")
            
            return tx_hash.hex()
        else:
            print(f"❌ 交易失败！状态: {receipt['status']}")
            print(f"   交易哈希: {tx_hash.hex()}")
            return f"交易失败: {tx_hash.hex()}"
            
    except Exception as e:
        print(f"❌ 借款交易执行失败: {e}")
        return f"执行失败: {str(e)}"

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

def supply_aave_v3_token(token_add, address, amount):
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
    # print(asyncio.run(supply_aave_v3_token(USDT_CONTRACT_ADDRESS_ETH, addr, 1000*10**6)))