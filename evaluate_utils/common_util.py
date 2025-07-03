import time
from eth_typing import ChecksumAddress
from web3 import Web3, HTTPProvider
from web3.types import TxParams
from eth_account.signers.local import LocalAccount
from dataset.constants import (
    ERC20_ABI, RPC_URL, PRIVATE_KEY,
    WETH_CONTRACT_ADDRESS_ETH
)

# 最小ABI
WETH_ABI = [
    {"inputs":[],"name":"deposit","outputs":[],"stateMutability":"payable","type":"function"}
]

w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

def send_transaction(tx: TxParams):
    tx.update({
        "nonce": w3.eth.get_transaction_count(addr),
        "chainId": w3.eth.chain_id,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

def wrap_eth_to_weth(amount_eth: float):
    """
    将ETH包装为WETH
    
    Args:
        amount_eth: 要包装的ETH数量
    """
    amount_in_wei = int(amount_eth * 10**18)
    
    # Wrap ETH to WETH
    weth = w3.eth.contract(address=Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH), abi=WETH_ABI)
    print(f"\nDepositing {amount_eth} ETH to WETH...")
    receipt = send_transaction(
        weth.functions.deposit().build_transaction({
            "from": addr,
            "value": amount_in_wei,
            "gas": 100_000
        })
    )
    print("Deposit complete, gas used:", receipt.gasUsed)


def approve_erc20(token_address: ChecksumAddress, spender: ChecksumAddress, amount: int):
    token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
    tx = token_contract.functions.approve(spender, amount).build_transaction({
        "from": addr,
        "gas": 100_000
    })
    receipt = send_transaction(tx)
    receipt = w3.eth.wait_for_transaction_receipt(receipt["transactionHash"])
    if receipt["status"] == 1:
        print(f"Approve successful: token={token_address}, spender={spender}, amount={amount}, tx_hash={receipt['transactionHash'].hex()}, gas_used={receipt['gasUsed']}")
    else:
        print(f"Approve failed: token={token_address}, spender={spender}, amount={amount}, tx_hash={receipt['transactionHash'].hex()}, gas_used={receipt['gasUsed']}")
    return receipt


    # INSERT_YOUR_CODE
def transfer_eth(to_address: str, amount_eth: float):
    """
    向指定账户转账ETH

    Args:
        to_address: 接收方地址（字符串）
        amount_eth: 转账ETH数量（float）
    """
    amount_in_wei = int(amount_eth * 10**18)
    tx = {
        "from": addr,
        "to": Web3.to_checksum_address(to_address),
        "value": amount_in_wei,
        "nonce": w3.eth.get_transaction_count(addr),
        "chainId": w3.eth.chain_id,
        "gas": 21000,
        "gasPrice": w3.eth.gas_price
    }
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt["status"] == 1:
        print(f"转账成功，tx_hash: {tx_hash.hex()}，gas_used: {receipt['gasUsed']}")
    else:
        print(f"转账失败，tx_hash: {tx_hash.hex()}，gas_used: {receipt['gasUsed']}")
    return receipt
