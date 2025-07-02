import json
from pathlib import Path
from evaluate_utils.morpho_util import morpho_contract
from web3 import Web3


# 向 MorphO 协议存入 1 ETH

from dataset.constants import USDT_CONTRACT_ADDRESS_ETH, WETH_CONTRACT_ADDRESS_ETH, MORPHO_CONTRACT_ADDRESS_ETH, RPC_URL, PRIVATE_KEY, ERC20_ABI
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

# 3. 调用 MorphO 的 supplyCollateral 方法存入 1 WETH 作为抵押品
def supply_weth_to_morpho(amount_wei):
    # 需要构造 MarketParams 结构体
    # loanToken=USDT (你想要借的代币), collateralToken=WETH (你要提供的抵押品)
    # 这里的配置是正确的：提供WETH作为抵押品来借USDT
    market_params = (
        Web3.to_checksum_address(USDT_CONTRACT_ADDRESS_ETH),  # loanToken - 你想要借的代币
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),  # collateralToken - 你提供的抵押品
        "0xe9eE579684716c7Bb837224F4c7BeEfA4f1F3d7f",         # oracle
        "0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC",         # irm
        915000000000000000                                   # lltv
    )
    
    print("=== MorphO Supply Collateral Transaction ===")
    print(f"存入抵押品数量: {amount_wei / 1e18} WETH")
    print(f"市场参数:")
    print(f"  loanToken (USDT): {market_params[0]}")
    print(f"  collateralToken (WETH): {market_params[1]}")
    print(f"  oracle: {market_params[2]}")
    print(f"  irm: {market_params[3]}")
    print(f"  lltv: {market_params[4]}")
    
    try:
        # supplyCollateral(MarketParams memory marketParams, uint256 assets, address onBehalf, bytes data)
        # 注意：这里使用supplyCollateral而不是supply，因为我们要提供抵押品
        tx = morpho_contract.functions.supplyCollateral(
            market_params,
            amount_wei,    # assets - 抵押品数量
            address,       # onBehalf
            b''           # data (空字节)
        ).build_transaction({
            "from": address,
            "nonce": w3.eth.get_transaction_count(address),
            "gas": 300000,
        })
        
        print(f"交易详情: {tx}")
        signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"交易已发送，哈希: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt['status'] == 1:
            print(f"✅ 交易成功！已向 MorphO 存入 {amount_wei / 1e18} WETH 作为抵押品")
            print(f"   交易哈希: {tx_hash.hex()}")
            print(f"   Gas 使用量: {receipt['gasUsed']}")
            print(f"   区块号: {receipt['blockNumber']}")
            return True
        else:
            print(f"❌ 交易失败！状态码: {receipt['status']}")
            print(f"   交易哈希: {tx_hash.hex()}")
            print(f"   可能的原因:")
            print(f"   1. 市场不存在")
            print(f"   2. 参数无效")
            print(f"   3. 授权不足")
            return False
            
    except Exception as e:
        print(f"❌ 交易执行失败: {e}")
        return False

def get_market_info(market_id):
    market_info = morpho_contract.functions.market(market_id).call()
    print(market_info)
    [total_supply_assets, total_supply_shares, total_borrow_assets, total_borrow_shares, last_update, fee] = market_info
    print(f"总供应资产: {total_supply_assets / 1e18} WETH")
    print(f"总供应份额: {total_supply_shares}")
    print(f"总借款资产: {total_borrow_assets / 1e18} WETH")
    print(f"总借款份额: {total_borrow_shares}")
    print(f"最后更新时间: {last_update}")
    print(f"费用: {fee}")
    return market_info

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
    从 MorphO 借出 100 USDT 到钱包

    本函数根据 ABI 规范，调用 borrow(MarketParams memory marketParams, uint256 assets, uint256 shares, address onBehalf, address receiver)
    其中 MarketParams 结构体为 (loanToken, collateralToken, oracle, irm, lltv)
    """

    # 100 USDT，USDT 是 6 位小数
    amount_wei = int(100 * 1e6)

    # 构造 MarketParams 结构体
    # 这些参数必须与 supply_usdt_to_morpho 时完全一致
    market_params = (
        Web3.to_checksum_address(USDT_CONTRACT_ADDRESS_ETH),  # loanToken
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),  # collateralToken
        "0xe9eE579684716c7Bb837224F4c7BeEfA4f1F3d7f",         # oracle
        "0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC",         # irm
        915000000000000000                                   # lltv
    )

    try:
        # 调用 borrow 函数
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
            print(f"✅ 成功从 MorphO 借出 100 USDT, 交易哈希: {tx_hash.hex()}")
        else:
            print(f"❌ 借款交易失败 (status: {receipt['status']})")
            print("可能的原因:")
            print("1. 没有足够的抵押品")
            print("2. 市场参数无效")
            print("3. 市场不存在或未激活")
            print("4. 超出借款限制")

        print(f"交易哈希: {tx_hash.hex()}")
        print(f"Gas 使用量: {receipt['gasUsed']}")
        return receipt

    except Exception as e:
        print(f"❌ 借款操作失败: {e}")
        print("\n💡 提示：要成功借款，您需要:")
        print("1. 先存入抵押品 (如 WETH)")
        print("2. 使用有效的市场参数 (真实的 oracle、IRM、LLTV)")
        print("3. 确保市场已创建并激活")
        print("4. 确保有足够的借款能力")
        return None




def get_morpho_weth_borrowable():
    """
    查询当前账户在 MorphO 上的位置信息
    """
    # 构造 MarketParams 结构体 - 必须与supply_weth_to_morpho中的参数完全一致
    market_params = (
        Web3.to_checksum_address(USDT_CONTRACT_ADDRESS_ETH),  # loanToken
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),  # collateralToken
        "0xe9eE579684716c7Bb837224F4c7BeEfA4f1F3d7f",         # oracle - 与supply函数保持一致
        "0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC",         # irm
        915000000000000000                                   # lltv - 与supply函数保持一致
    )
    
    try:
        # 计算市场ID (通过hash计算)
        # 将market_params编码后计算hash作为market ID
        encoded_params = w3.codec.encode(['address', 'address', 'address', 'address', 'uint256'], 
                                       [market_params[0], market_params[1], market_params[2], market_params[3], market_params[4]])
        market_id = w3.keccak(encoded_params)
        
        print(f"市场ID: {market_id.hex()}")
        print(f"市场参数:")
        print(f"  loanToken: {market_params[0]}")
        print(f"  collateralToken: {market_params[1]}")
        print(f"  oracle: {market_params[2]}")
        print(f"  irm: {market_params[3]}")
        print(f"  lltv: {market_params[4]}")
        
        # 查询账户在该市场的位置: position(market_id, address)
        position_info = morpho_contract.functions.position(market_id, address).call()
        supply_shares, borrow_shares, collateral = position_info
        
        print(f"账户位置信息:")
        print(f"  供应份额 (Supply Shares): {supply_shares}")
        print(f"  借款份额 (Borrow Shares): {borrow_shares}")
        print(f"  抵押品 (Collateral): {collateral / 1e18} WETH")
        
        # 查询市场总体信息
        market_info = morpho_contract.functions.market(market_id).call()
        total_supply_assets, total_supply_shares, total_borrow_assets, total_borrow_shares, last_update, fee = market_info
        
        print(f"市场信息:")
        print(f"  总供应资产: {total_supply_assets / 1e6} USDT")  # USDT是6位小数
        print(f"  总供应份额: {total_supply_shares}")
        print(f"  总借款资产: {total_borrow_assets / 1e6} USDT") 
        print(f"  总借款份额: {total_borrow_shares}")
        print(f"  最后更新时间: {last_update}")
        print(f"  费用: {fee}")
        
        return {
            'supply_shares': supply_shares,
            'borrow_shares': borrow_shares,
            'collateral': collateral,
            'market_info': market_info,
            'market_id': market_id.hex()
        }
        
    except Exception as e:
        print(f"查询账户位置信息时出错: {e}")
        return None


if __name__ == "__main__":
    amount = int(1e18)  # 1 ETH (WETH)
    
    print("=== MorphO 抵押品存入流程 ===")
    
    # 1. 检查并包装ETH为WETH（如果需要）
    # wrap_eth_if_needed(amount)
    
    # 2. 授权MorphO合约使用WETH
    # print("\n📋 步骤1: 检查WETH授权...")
    approve_weth_to_morpho(amount)
    
    # 3. 存入WETH作为抵押品
    print("\n📋 步骤2: 存入WETH作为抵押品...")
    success = supply_weth_to_morpho(amount)
    
    if success:
        print("\n📋 步骤3: 查询账户位置信息...")
        # 查询账户信息
        result = get_morpho_weth_borrowable()
        
        if result and result['collateral'] > 0:
            print(f"\n✅ 成功！你现在有 {result['collateral'] / 1e18} WETH 抵押品")
        else:
            print("\n⚠️  警告：查询结果显示抵押品为0，可能需要等待几个区块确认")
    else:
        print("\n❌ 抵押品存入失败，跳过查询步骤")
    
    print("\n=== 流程完成 ===")
    
    # 注释掉借款功能，因为需要先有抵押品
    borrow_weth_from_morpho(amount)
