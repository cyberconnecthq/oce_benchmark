from eth_typing import ChecksumAddress
from dataset.constants import (
    MORPHO_CONTRACT_ADDRESS_ETH,
    MORPHO_VAULT_ABI, 
    RPC_URL, 
    PRIVATE_KEY, 
    ERC20_ABI,
    USDC_CONTRACT_ADDRESS_ETH,
    WETH_CONTRACT_ADDRESS_ETH,
    MORPHO_CONTRACT_ABI
)
import json
from web3 import Web3

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address
# 初始化 WETH 合约实例


weth = w3.eth.contract(address=Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH), abi=ERC20_ABI)


def load_morpho_contract(w3: Web3):
    """
    加载 Morpho 合约实例

    参数:
        w3 (Web3): 已连接的 Web3 实例

    返回:
        Contract: Morpho 合约对象
    """
    contract = w3.eth.contract(address=Web3.to_checksum_address(MORPHO_CONTRACT_ADDRESS_ETH), abi=MORPHO_CONTRACT_ABI)
    return contract


morpho_contract = load_morpho_contract(w3)

def get_token_balance(token_address, holder_address):
    """
    查询Morpho合约中持有某个ERC20代币的数量

    参数:
        token_address (str): 代币合约地址
        holder_address (str): 持币地址（如Morpho合约地址）

    返回:
        int: 代币余额（单位：最小单位）
    """
    # ERC20 ABI 只需要 balanceOf 方法
    erc20_abi = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }
    ]
    token_contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc20_abi)
    balance = token_contract.functions.balanceOf(Web3.to_checksum_address(holder_address)).call()
    return balance


def approve_weth_to_morpho(amount_wei: int, address: ChecksumAddress):
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
        print("Approved MorphO contract to spend 1 WETH")
    else:
        print("MorphO approval is sufficient")
    

def supply_weth_to_morpho(amount_wei: int, from_address:ChecksumAddress, market_params: tuple):
    print("=== Morpho Supply Collateral Transaction ===")
    print(f"Supply amount: {amount_wei / 1e18} WETH")
    print("MarketParams:")
    print(f"  loanToken (USDT): {market_params[0]}")
    print(f"  collateralToken (WETH): {market_params[1]}")
    print(f"  oracle: {market_params[2]}")
    print(f"  irm: {market_params[3]}")
    print(f"  lltv: {market_params[4]}")

    try:
        # supplyCollateral(MarketParams memory marketParams, uint256 assets, address onBehalf, bytes data)
        tx = morpho_contract.functions.supplyCollateral(
            market_params,
            amount_wei,    # assets
            from_address,  # onBehalf
            b''            # data (empty bytes)
        ).build_transaction({
            "from": from_address,
            "nonce": w3.eth.get_transaction_count(from_address),
            "gas": 800000,
        })

        print(f"Transaction details: {tx}")
        signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"Transaction sent, hash: {tx_hash.hex()}")

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt['status'] == 1:
            print(f"✅ Success! Supplied {amount_wei / 1e18} WETH as collateral to Morpho.")
            print(f"   Tx hash: {tx_hash.hex()}")
            print(f"   Gas used: {receipt['gasUsed']}")
            print(f"   Block number: {receipt['blockNumber']}")
            return True
        else:
            print(f"❌ Transaction failed! Status: {receipt['status']}")
            print(f"   Tx hash: {tx_hash.hex()}")
            print("   Possible reasons:")
            print("   1. Market does not exist")
            print("   2. Invalid parameters")
            print("   3. Insufficient approval")
            return False

    except Exception as e:
        print(f"❌ Transaction execution failed: {e}")
        return False

def borrow_usdt_from_morpho(amount_usdt_wei: int, from_address, market_params: tuple):
    """
    Borrow USDT from Morpho protocol to wallet.

    :param amount_usdt_wei: Borrow amount (in smallest unit, USDT is 1e6)
    :param from_address: Borrower address
    :param market_params: MarketParams tuple (loanToken, collateralToken, oracle, irm, lltv)
    :return: Transaction receipt or None
    """
    print("=== Morpho Borrow Transaction ===")
    print(f"Borrow amount: {amount_usdt_wei / 1e6} USDT")
    print("MarketParams:")
    print(f"  loanToken (USDT): {market_params[0]}")
    print(f"  collateralToken (WETH): {market_params[1]}")
    print(f"  oracle: {market_params[2]}")
    print(f"  irm: {market_params[3]}")
    print(f"  lltv: {market_params[4]}")

    try:
        # borrow(MarketParams memory marketParams, uint256 assets, uint256 shares, address onBehalf, address receiver)
        tx = morpho_contract.functions.borrow(
            market_params,
            amount_usdt_wei,  # assets
            0,                # shares (0 means no share limit)
            from_address,     # onBehalf
            from_address      # receiver
        ).build_transaction({
            "from": from_address,
            "nonce": w3.eth.get_transaction_count(from_address),
            "gas": 800000,
        })

        print(f"Transaction details: {tx}")
        signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"Transaction sent, hash: {tx_hash.hex()}")

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt['status'] == 1:
            print(f"✅ Successfully borrowed {amount_usdt_wei / 1e6} USDT from Morpho")
            print(f"   Tx hash: {tx_hash.hex()}")
            print(f"   Gas used: {receipt['gasUsed']}")
            print(f"   Block number: {receipt['blockNumber']}")
            return receipt
        else:
            print(f"❌ Borrow transaction failed (status: {receipt['status']})")
            print("Possible reasons:")
            print("1. Not enough collateral")
            print("2. Invalid market parameters")
            print("3. Market does not exist or is not active")
            print("4. Borrow limit exceeded")
            return None

    except Exception as e:
        print(f"❌ Borrow operation failed: {e}")
        print("\n💡 Tips for successful borrowing:")
        print("1. Supply collateral (e.g. WETH) first")
        print("2. Use valid market parameters (real oracle, IRM, LLTV)")
        print("3. Make sure the market is created and active")
        print("4. Make sure you have enough borrowing power")
        return None



def deposit_to_vault(vault_address: ChecksumAddress, amount_usdc: float, receiver: ChecksumAddress, ):
    """
    向指定的 Morpho Vault 存入 USDC

    :param vault_address: 金库合约地址
    :param amount_usdc: 存入的 USDC 数量（float，单位为USDC）
    :param receiver: 接收 shares 的地址
    :param w3: Web3 实例
    :param PRIVATE_KEY: 发送者私钥
    :return: 交易回执或 None
    """
    # 加载 ABI

    vault_contract = w3.eth.contract(address=vault_address, abi=MORPHO_VAULT_ABI)

    # 获取 USDC 地址
    usdc_address = Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH)
    usdc_contract = w3.eth.contract(address=usdc_address, abi=[
        {
            "constant": False,
            "inputs": [
                {"name": "_spender", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        }
    ])

    # 获取 USDC 精度
    usdc_decimals = usdc_contract.functions.decimals().call()
    amount_usdc_wei = int(amount_usdc * (10 ** usdc_decimals))

    # 获取当前账户地址
    from_address = addr

    # 先授权
    try:
        approve_tx = usdc_contract.functions.approve(
            vault_address,
            amount_usdc_wei
        ).build_transaction({
            "from": from_address,
            "nonce": w3.eth.get_transaction_count(from_address),
            "gas": 100000,
        })
        signed_approve = w3.eth.account.sign_transaction(approve_tx, private_key=PRIVATE_KEY)
        approve_tx_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
        print(f"授权 USDC 中，交易哈希: {approve_tx_hash.hex()}")
        approve_receipt = w3.eth.wait_for_transaction_receipt(approve_tx_hash)
        if approve_receipt['status'] != 1:
            print("❌ 授权 USDC 失败")
            return None
    except Exception as e:
        print(f"❌ 授权 USDC 失败: {e}")
        return None

    # 调用 deposit
    try:
        deposit_tx = vault_contract.functions.deposit(
            amount_usdc_wei,
            from_address
        ).build_transaction({
            "from": from_address,
            "nonce": w3.eth.get_transaction_count(from_address),
            "gas": 30000000,
        })
        signed_deposit = w3.eth.account.sign_transaction(deposit_tx, private_key=PRIVATE_KEY)
        deposit_tx_hash = w3.eth.send_raw_transaction(signed_deposit.raw_transaction)
        print(f"存入 USDC 中，交易哈希: {deposit_tx_hash.hex()}")
        deposit_receipt = w3.eth.wait_for_transaction_receipt(deposit_tx_hash)
        if deposit_receipt['status'] == 1:
            print(f"✅ 成功存入 {amount_usdc} USDC 到 Morpho Vault")
            print(f"   Tx hash: {deposit_tx_hash.hex()}")
            print(f"   Gas used: {deposit_receipt['gasUsed']}")
            print(f"   Block number: {deposit_receipt['blockNumber']}")
            return deposit_receipt
        else:
            print(f"❌ 存入 USDC 失败 (status: {deposit_receipt['status']})")
            return None
    except Exception as e:
        print(f"❌ 存入 USDC 失败: {e}")
        return None