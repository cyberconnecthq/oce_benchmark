import json
from typing import List, Optional
from pydantic import BaseModel

from web3 import Web3

# 定义 trade 的 Pydantic 类型
class Trade(BaseModel):
    sellTokenIndex: int
    buyTokenIndex: int
    receiver: str
    sellAmount: int
    buyAmount: int
    validTo: int
    appData: str  # bytes32, 传入hex字符串
    feeAmount: int
    flags: int
    executedAmount: int
    signature: str  # bytes, 传入hex字符串

# 加载 Cow Protocol ABI
def load_cow_abi():
    with open("abi/cow_protocol_abi.json", "r") as f:
        return json.load(f)

# 初始化 Cow Protocol 合约
def get_cow_contract(w3, contract_address):
    abi = load_cow_abi()
    return w3.eth.contract(address=contract_address, abi=abi)

# swap 功能
def swap(w3, contract_address, account, trade: Trade, tokens: List[str], gas=500000):
    """
    trade: Trade对象
    tokens: 代币地址列表
    """
    contract = get_cow_contract(w3, contract_address)
    # 构造 trade tuple
    trade_tuple = (
        trade.sellTokenIndex,
        trade.buyTokenIndex,
        trade.receiver,
        int(trade.sellAmount),
        int(trade.buyAmount),
        int(trade.validTo),
        bytes.fromhex(trade.appData[2:]) if trade.appData.startswith("0x") else bytes.fromhex(trade.appData),
        int(trade.feeAmount),
        int(trade.flags),
        int(trade.executedAmount),
        bytes.fromhex(trade.signature[2:]) if trade.signature.startswith("0x") else bytes.fromhex(trade.signature)
    )
    tx = contract.functions.swap(
        tokens,
        trade_tuple
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": gas,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash.hex()

# addliquidity 功能（Cow Protocol 本身不直接支持LP操作，这里假设通过settle函数实现多笔swap/LP操作，需根据实际情况调整）
def addliquidity(w3, contract_address, account, tokens: List[str], clearing_prices: List[int], trades: List[Trade], interactions, gas=1000000):
    """
    tokens: 代币地址列表
    clearing_prices: 清算价格列表
    trades: Trade对象列表
    interactions: GPv2Interaction.Data[][3]，见ABI
    """
    contract = get_cow_contract(w3, contract_address)
    trades_tuple = []
    for trade in trades:
        trades_tuple.append((
            trade.sellTokenIndex,
            trade.buyTokenIndex,
            trade.receiver,
            int(trade.sellAmount),
            int(trade.buyAmount),
            int(trade.validTo),
            bytes.fromhex(trade.appData[2:]) if trade.appData.startswith("0x") else bytes.fromhex(trade.appData),
            int(trade.feeAmount),
            int(trade.flags),
            int(trade.executedAmount),
            bytes.fromhex(trade.signature[2:]) if trade.signature.startswith("0x") else bytes.fromhex(trade.signature)
        ))
    tx = contract.functions.settle(
        tokens,
        clearing_prices,
        trades_tuple,
        interactions
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": gas,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash.hex()

# removeliquidity 功能（同上，通常通过settle或自定义interaction实现）
def removeliquidity(w3, contract_address, account, tokens: List[str], clearing_prices: List[int], trades: List[Trade], interactions, gas=1000000):
    """
    tokens: 代币地址列表
    clearing_prices: 清算价格列表
    trades: Trade对象列表
    interactions: GPv2Interaction.Data[][3]，见ABI
    """
    contract = get_cow_contract(w3, contract_address)
    trades_tuple = []
    for trade in trades:
        trades_tuple.append((
            trade.sellTokenIndex,
            trade.buyTokenIndex,
            trade.receiver,
            int(trade.sellAmount),
            int(trade.buyAmount),
            int(trade.validTo),
            bytes.fromhex(trade.appData[2:]) if trade.appData.startswith("0x") else bytes.fromhex(trade.appData),
            int(trade.feeAmount),
            int(trade.flags),
            int(trade.executedAmount),
            bytes.fromhex(trade.signature[2:]) if trade.signature.startswith("0x") else bytes.fromhex(trade.signature)
        ))
    tx = contract.functions.settle(
        tokens,
        clearing_prices,
        trades_tuple,
        interactions
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": gas,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash.hex()

