
from ens import ENS
from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount

# ETH主网RPC
ETH_RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"  # 默认anvil账户

# 连接ETH主网
w3 = Web3(HTTPProvider(ETH_RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

# ENS注册器合约地址和ABI
ENS_REGISTRAR_ADDRESS = "0x283Af0B28c62C092C9727F1Ee09c02CA627EB7F5"
ENS_REGISTRAR_ABI = [
    {
        "inputs": [
            {"name": "name", "type": "string"},
            {"name": "owner", "type": "address"},
            {"name": "duration", "type": "uint256"},
            {"name": "resolver", "type": "address"}
        ],
        "name": "register",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]

def mint_ens_domain(domain_name: str, duration_years: int = 1):
    """
    注册一个.eth域名
    """
    # 移除.eth后缀(如果有)
    if domain_name.endswith(".eth"):
        domain_name = domain_name[:-4]
        
    # 创建合约实例
    registrar = w3.eth.contract(
        address=w3.to_checksum_address(ENS_REGISTRAR_ADDRESS),
        abi=ENS_REGISTRAR_ABI
    )
    
    # 准备交易参数
    duration = duration_years * 365 * 24 * 60 * 60  # 转换为秒
    resolver = "0x4976fb03C32e5B8cfe2b6cCB31c09Ba78EBaBa41"  # ENS公共解析器
    
    # 构建交易
    nonce = w3.eth.get_transaction_count(addr)
    tx = registrar.functions.register(
        domain_name,
        addr,
        duration,
        resolver
    ).build_transaction({
        "from": addr,
        "value": w3.to_wei(0.01, "ether"),  # 注册费用(实际费用根据名称长度变化)
        "gas": 300000,
        "gasPrice": w3.eth.gas_price,
        "nonce": nonce,
        "chainId": w3.eth.chain_id
    })
    
    # 签名并发送交易
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"ENS域名注册交易已发送，交易哈希: {tx_hash.hex()}")
    
    # 等待交易确认
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(tx_receipt.values())
    if tx_receipt["status"] == 1:
        print(f"成功注册ENS域名: {domain_name}.eth")
    else:
        print("ENS域名注册失败")

if __name__ == "__main__":
    domain_name = "example123"  # 替换为你想注册的域名
    mint_ens_domain(domain_name)
