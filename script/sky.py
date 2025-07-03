import json
from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import (
    RPC_URL,
    PRIVATE_KEY,
    ERC20_ABI,
    USDS_CONTRACT_ADDRESS_ETH,
    SUSDS_CONTRACT_ADDRESS_ETH
)

# 初始化 web3
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

# sUSDS实现ERC-4626标准，包含deposit功能
SUSDS_ABI = [
    {
        "inputs": [
            {"name": "assets", "type": "uint256"},
            {"name": "receiver", "type": "address"}
        ],
        "name": "deposit",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "assets", "type": "uint256"},
            {"name": "receiver", "type": "address"},
            {"name": "referral", "type": "uint16"}
        ],
        "name": "deposit",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# 初始化合约实例
usds_contract = w3.eth.contract(
    address=Web3.to_checksum_address(USDS_CONTRACT_ADDRESS_ETH), 
    abi=ERC20_ABI
)
susds_contract = w3.eth.contract(
    address=Web3.to_checksum_address(SUSDS_CONTRACT_ADDRESS_ETH), 
    abi=SUSDS_ABI
)

def supply(amount_usds: float, referral: int = 0):
    """
    向Sky.money供应USDS，获得sUSDS（Savings USDS）代币以获得Sky Savings Rate收益
    
    Args:
        amount_usds (float): 要供应的USDS数量（以USDS为单位，18位小数）
        referral (int): 推荐码，用于跟踪存款来源（可选，默认为0）
    
    Returns:
        str: 交易哈希或错误信息
    """
    try:
        print("=== Sky.money USDS Supply Transaction ===")
        print(f"供应数量: {amount_usds} USDS")
        print(f"推荐码: {referral}")
        
        # 转换为最小单位（USDS是18位小数）
        amount_wei = int(amount_usds * 10**18)
        
        # 检查USDS余额
        usds_balance = usds_contract.functions.balanceOf(addr).call()
        print(f"当前USDS余额: {usds_balance / 10**18} USDS")
        
        if usds_balance < amount_wei:
            return f"❌ 余额不足！需要 {amount_usds} USDS，但只有 {usds_balance / 10**18} USDS"
        
        # 检查并设置授权
        allowance = usds_contract.functions.allowance(addr, SUSDS_CONTRACT_ADDRESS_ETH).call()
        if allowance < amount_wei:
            print("授权sUSDS合约使用USDS...")
            approve_tx = usds_contract.functions.approve(
                SUSDS_CONTRACT_ADDRESS_ETH, 
                amount_wei * 2  # 授权更多以避免频繁授权
            ).build_transaction({
                "from": addr,
                "nonce": w3.eth.get_transaction_count(addr),
                "gas": 100000,
                "gasPrice": w3.to_wei("20", "gwei")
            })
            
            signed_approve = w3.eth.account.sign_transaction(approve_tx, private_key=PRIVATE_KEY)
            approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
            w3.eth.wait_for_transaction_receipt(approve_hash)
            print("✅ 授权完成")
        
        # 构建存款交易 - 使用带推荐码的deposit函数
        if referral > 0:
            deposit_tx = susds_contract.functions.deposit(
                amount_wei,    # assets: 存入的USDS数量
                addr,          # receiver: 接收sUSDS的地址
                referral       # referral: 推荐码
            ).build_transaction({
                "from": addr,
                "nonce": w3.eth.get_transaction_count(addr),
                "gas": 300000,
                "gasPrice": w3.to_wei("20", "gwei")
            })
        else:
            # 使用不带推荐码的标准deposit函数
            deposit_tx = susds_contract.functions.deposit(
                amount_wei,    # assets: 存入的USDS数量
                addr           # receiver: 接收sUSDS的地址
            ).build_transaction({
                "from": addr,
                "nonce": w3.eth.get_transaction_count(addr),
                "gas": 300000,
                "gasPrice": w3.to_wei("20", "gwei")
            })
        
        print(f"交易详情: {deposit_tx}")
        
        # 签名并发送交易
        signed_tx = w3.eth.account.sign_transaction(deposit_tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"交易已发送，哈希: {tx_hash.hex()}")
        
        # 等待交易确认
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt['status'] == 1:
            # 检查新的sUSDS余额
            susds_balance = susds_contract.functions.balanceOf(addr).call()
            print(f"✅ 成功！向Sky.money供应了 {amount_usds} USDS")
            print(f"   获得sUSDS余额: {susds_balance / 10**18:.6f} sUSDS")
            print(f"   交易哈希: {tx_hash.hex()}")
            print(f"   Gas使用量: {receipt['gasUsed']}")
            print(f"   区块号: {receipt['blockNumber']}")
            print(f"   现在开始赚取Sky Savings Rate收益！")
            return tx_hash.hex()
        else:
            print(f"❌ 交易失败！状态: {receipt['status']}")
            print(f"   交易哈希: {tx_hash.hex()}")
            return f"交易失败: {tx_hash.hex()}"
            
    except Exception as e:
        print(f"❌ 交易执行失败: {e}")
        return f"执行失败: {str(e)}"

if __name__ == "__main__":
    # 示例：供应10 USDS到Sky.money
    # result = supply(10.0)
    # print(f"交易结果: {result}")


    tx = {"chainId": 1, "data": "0x095ea7b30000000000000000000000003225737a9bbb6473cb4a45b7244aca2befdb276a000000000000000000000000000000000000000000000000000000000001d4c0", "from": "0x2A804F0c969a4d5c35E551B690Db28371f833567", "gas": 56361, "to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "value": 0, "nonce": 26, "maxFeePerGas": 1640891266, "maxPriorityFeePerGas": 14}
    from execute import sign_and_send_transaction

    print(sign_and_send_transaction(tx, account, w3, bind_address=None))