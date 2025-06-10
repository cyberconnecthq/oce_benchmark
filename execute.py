import os
from web3 import Web3, HTTPProvider
from web3.types import TxParams
from eth_account.signers.local import LocalAccount



def sign_and_send_transaction(tx: TxParams, account:LocalAccount, w3:Web3) -> tuple[bool, int]:
    tx.update({
        "nonce": w3.eth.get_transaction_count(account.address),
        "chainId": w3.eth.chain_id,
    })
    # 检查tx中是否有gasPrice
    if "gasPrice" not in tx:
        # 如果没有gasPrice，则使用maxFeePerGas和maxPriorityFeePerGas
        if "maxFeePerGas" not in tx and "maxPriorityFeePerGas" not in tx:
            tx['gasPrice'] = w3.to_wei(30, 'gwei')
    if 'gas' not in tx:
        tx['gas'] = 800_000
    print(tx)
    sign_tx = account.sign_transaction(transaction_dict=tx)
    tx_hash = w3.eth.send_raw_transaction(sign_tx.raw_transaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if tx_receipt["status"] == 1:
        print("交易执行成功!")
        print(f"使用的 gas: {tx_receipt['gasUsed']}")
        print(f"区块号: {tx_receipt['blockNumber']}")
        return True, tx_receipt["gasUsed"]
    else:
        print("交易执行失败!")
        print(tx)
        print(f"交易哈希: {tx_receipt['transactionHash'].hex()}")
        return False, 0