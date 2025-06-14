import json
from pathlib import Path
from evaluate_utils.morpho_util import morpho_contract
from web3 import Web3


# 向 MorphO 协议存入 1 ETH

from dataset.constants import WETH_CONTRACT_ADDRESS_ETH, MORPHO_CONTRACT_ADDRESS_ETH, RPC_URL, PRIVATE_KEY, ERC20_ABI
from web3 import Web3
from eth_account import Account

# 初始化 web3 和账户
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
address = account.address

script_dir = Path(__file__).parent
abi_dir = script_dir.parent / "abi"
with open(abi_dir / "erc20_abi.json") as f:
    ERC20_ABI = json.load(f)
# 获取 WETH 合约实例
weth = w3.eth.contract(address=Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH), abi=ERC20_ABI)

# 1. 先检查账户 WETH 余额是否足够，否则先将 1 ETH 包装成 WETH
def wrap_eth_if_needed(amount_wei):
    weth_balance = weth.functions.balanceOf(address).call()
    if weth_balance < amount_wei:
        # 包装 1 ETH 成 WETH
        func = weth.functions.deposit()
        tx = func.build_transaction({
            "from": address,
            "to": WETH_CONTRACT_ADDRESS_ETH,
            "value": amount_wei,
            "gas": 100000,
            "nonce": w3.eth.get_transaction_count(address),
        })
        signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print("已将 1 ETH 包装为 WETH")
    else:
        print("WETH 余额充足，无需包装")

# 2. 授权 MorphO 合约支配 1 WETH
def approve_weth_to_morpho(amount_wei):
    allowance = weth.functions.allowance(address, MORPHO_CONTRACT_ADDRESS_ETH).call()
    if allowance < amount_wei:
        tx = weth.functions.approve(MORPHO_CONTRACT_ADDRESS_ETH, amount_wei).build_transaction({
            "from": address,
            "nonce": w3.eth.get_transaction_count(address),
            "gas": 60000,
        })
        signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print("已授权 MorphO 合约支配 1 WETH")
    else:
        print("MorphO 授权已足够")

# 3. 调用 MorphO 的 supply 方法存入 1 WETH
def supply_weth_to_morpho(amount_wei):
    # 需要构造 MarketParams 结构体
    # 这里假设 loanToken=WETH，collateralToken=0x0(无抵押)，oracle/irm/lltv 需根据实际合约配置
    # 这里只做演示，实际参数请根据合约 ABI 和部署情况调整
    # 你需要根据 morpho_abi.json 里的 MarketParams 结构体定义来填写参数
    # 下面是一个示例（参数需根据实际情况填写）
    market_params = (
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),  # loanToken
        "0x0000000000000000000000000000000000000000",         # collateralToken
        "0xbD60A6770b27E084E8617335ddE769241B0e71D8",         # oracle
        "0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC",         # irm
        0                                                     # lltv
    )
    # supply(MarketParams memory marketParams, uint256 assets, uint256 shares, address onBehalf, bytes data)
    tx = morpho_contract.functions.supply(
        market_params,
        amount_wei,    # assets
        0,            # shares (0 表示不限制shares)
        address,      # onBehalf
        b''           # data (空字节)
    ).build_transaction({
        "from": address,
        "nonce": w3.eth.get_transaction_count(address),
        "gas": 300000,
    })
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(receipt.values())
    print(f"已向 MorphO 存入 1 WETH, 交易哈希: {tx_hash.hex()}")


def withdraw_weth_from_morpho(amount_wei):
    """
    从 MorphO 合约提取指定数量的 WETH 到钱包
    """
    # 构造 MarketParams 结构体
    market_params = (
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),  # loanToken
        "0x0000000000000000000000000000000000000000",         # collateralToken
        "0x0000000000000000000000000000000000000000",         # oracle
        "0x0000000000000000000000000000000000000000",         # irm
        0                                                     # lltv
    )
    # withdraw(MarketParams memory marketParams, uint256 assets, uint256 shares, address onBehalf, address receiver)
    tx = morpho_contract.functions.withdraw(
        market_params,
        amount_wei,    # assets
        0,             # shares (0 表示不限制shares)
        address,       # onBehalf
        address        # receiver (接收代币的地址)
    ).build_transaction({
        "from": address,
        "nonce": w3.eth.get_transaction_count(address),
        "gas": 300000,
    })
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(receipt.values())
    print(f"已从 MorphO 提取 {amount_wei / 1e18} WETH, 交易哈希: {tx_hash.hex()}")


def borrow_weth_from_morpho(amount_wei):
    """
    从 MorphO 借出指定数量的 WETH 到钱包
    
    注意：这个函数很可能会失败，因为：
    1. 借款需要足够的抵押品
    2. 当前使用的市场参数（oracle、irm、lltv）都是零值，可能不是有效的市场
    3. 在真实环境中，需要使用实际的预言机地址和利率模型
    """
    # 构造 MarketParams 结构体
    # 警告：这些参数可能无效，仅用于测试
    market_params = (
        "0xdAC17F958D2ee523a2206206994597C13D831ec7", # collateralToken (无抵押品)
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),  # loanToken
        "0xe9eE579684716c7Bb837224F4c7BeEfA4f1F3d7f",         # oracle (需要真实预言机)
        "0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC",         # irm (需要真实利率模型)
        0                                                     # lltv (需要真实LLTV)
    )
    
    try:
        # borrow(MarketParams memory marketParams, uint256 assets, uint256 shares, address onBehalf, address receiver)
        tx = morpho_contract.functions.borrow(
            market_params,
            amount_wei,    # assets
            0,             # shares (0 表示不限制shares)
            address,       # onBehalf
            address        # receiver (接收代币的地址)
        ).build_transaction({
            "from": address,
            "nonce": w3.eth.get_transaction_count(address),
            "gas": 300000,
        })
        signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt['status'] == 1:
            print(f"✅ 成功从 MorphO 借出 {amount_wei / 1e18} WETH, 交易哈希: {tx_hash.hex()}")
        else:
            print(f"❌ 借款交易失败 (status: {receipt['status']})")
            print("可能的原因:")
            print("1. 没有足够的抵押品")
            print("2. 市场参数无效（oracle、irm、lltv 为零）")
            print("3. 市场不存在或未激活")
            print("4. 超出借款限制")
            
        print(f"交易哈希: {tx_hash.hex()}")
        print(f"Gas 使用量: {receipt['gasUsed']}")
        return receipt
        
    except Exception as e:
        print(f"❌ 借款操作失败: {e}")
        print("\n💡 提示：要成功借款，您需要:")
        print("1. 先存入抵押品 (如 ETH 或其他代币)")
        print("2. 使用有效的市场参数 (真实的 oracle、IRM、LLTV)")
        print("3. 确保市场已创建并激活")
        print("4. 确保有足够的借款能力")
        return None

def get_morpho_weth_borrowable():
    """
    查询当前账户在 MorphO 上的位置信息
    """
    # 构造 MarketParams 结构体
    market_params = (
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),  # loanToken
        "0x0000000000000000000000000000000000000000",         # collateralToken
        "0xbD60A6770b27E084E8617335ddE769241B0e71D8",         # oracle
        "0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC",         # irm
        0                                                     # lltv
    )
    
    try:
        # 计算市场ID (通过hash计算)
        # 将market_params编码后计算hash作为market ID
        encoded_params = w3.codec.encode(['address', 'address', 'address', 'address', 'uint256'], 
                                       [market_params[0], market_params[1], market_params[2], market_params[3], market_params[4]])
        market_id = w3.keccak(encoded_params)
        
        # 查询账户在该市场的位置: position(market_id, address)
        position_info = morpho_contract.functions.position(market_id, address).call()
        supply_shares, borrow_shares, collateral = position_info
        
        print(f"账户位置信息:")
        print(f"  供应份额 (Supply Shares): {supply_shares}")
        print(f"  借款份额 (Borrow Shares): {borrow_shares}")
        print(f"  抵押品 (Collateral): {collateral}")
        
        # 查询市场总体信息
        market_info = morpho_contract.functions.market(market_id).call()
        total_supply_assets, total_supply_shares, total_borrow_assets, total_borrow_shares, last_update, fee = market_info
        
        print(f"市场信息:")
        print(f"  总供应资产: {total_supply_assets / 1e18} WETH")
        print(f"  总供应份额: {total_supply_shares}")
        print(f"  总借款资产: {total_borrow_assets / 1e18} WETH") 
        print(f"  总借款份额: {total_borrow_shares}")
        
        return {
            'supply_shares': supply_shares,
            'borrow_shares': borrow_shares,
            'collateral': collateral,
            'market_info': market_info
        }
        
    except Exception as e:
        print(f"查询账户位置信息时出错: {e}")
        return None


if __name__ == "__main__":
    amount = int(1e18)  # 1 ETH (WETH)
    # wrap_eth_if_needed(amount)
    # approve_weth_to_morpho(amount)
    # supply_weth_to_morpho(amount)

    borrow_weth_from_morpho(amount)

    get_morpho_weth_borrowable()
