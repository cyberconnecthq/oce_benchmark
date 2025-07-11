import os
from typing import Optional
from eth_account import Account
from web3 import Web3, HTTPProvider
from web3.types import TxParams
from eth_account.signers.local import LocalAccount



def sign_and_send_transaction(tx: TxParams, account:LocalAccount, w3:Web3, bind_address:Optional[str] = None) -> tuple[bool, int]:
    # 去除所有value为None的字段
    tx = {k: v for k, v in tx.items() if v is not None}
    if not bind_address:
        original_from_addr = tx.get("from", None)
        if original_from_addr:
            to_replace_addr = original_from_addr.lower()[2:]
            replace_addr = account.address.lower()[2:]
            tx["data"] = tx["data"].replace(to_replace_addr, replace_addr)
        tx.update({
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": w3.eth.chain_id,
            "from": w3.to_checksum_address(account.address),
            "to": w3.to_checksum_address(tx.get("to", "")),
        })
    
    else:
        account = Account.from_key(os.environ.get("REAL_PRIVATE_KEY", None))
        tx.update({
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": w3.eth.chain_id,
            "to": w3.to_checksum_address(tx.get("to", "")),
            "from":w3.to_checksum_address(account.address)
        })

    if tx.get('to', "") == "":
        print("Transaction failed! No 'to' address specified.")
        return False, 0

    # Check if gasPrice is in tx
    if "maxFeePerGas" in tx and "maxPriorityFeePerGas" in tx:
    # INSERT_YOUR_CODE
    # 删除 gas 和 gasPrice 字段
        tx.pop('gasPrice', None)
    elif "maxFeePerGas" not in tx and "maxPriorityFeePerGas" not in tx:
        tx['gasPrice'] = w3.to_wei(30, 'gwei')
        tx['gas'] = 800_000
        
    tx['gas']*=2
        
    print(tx)
    sign_tx = account.sign_transaction(transaction_dict=tx)
    tx_hash = w3.eth.send_raw_transaction(sign_tx.raw_transaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if tx_receipt["status"] == 1:
        print("Transaction succeeded!")
        print(f"Gas used: {tx_receipt['gasUsed']}")
        print(f"Block number: {tx_receipt['blockNumber']}")
        return True, tx_receipt["gasUsed"]
    else:
        print("Transaction failed!")
        print(tx)
        print(f"Transaction hash: {tx_receipt['transactionHash'].hex()}")
        print(tx_receipt.values())
        return False, 0


if __name__ == "__main__":
    from dataset.constants import PRIVATE_KEY
    w3 = Web3(HTTPProvider("http://127.0.0.1:8545"))
    account = w3.eth.account.from_key(PRIVATE_KEY)
    tx = {'to': '0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb', 'from': '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266', 'value': 0, 'data': '0x238d6579000000000000000000000000dac17f958d2ee523a2206206994597c13d831ec7000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000e9ee579684716c7bb837224f4c7beefa4f1f3d7f000000000000000000000000870ac11d48b15db9a138cf899d20f13f79ba00bc0000000000000000000000000000000000000000000000000cb2bba6f17b800000000000000000000000000000000000000000000000000000005af3107a4000000000000000000000000000f39fd6e51aad88f6f4ce6ab8827279cfffb9226600000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000', 'maxPriorityFeePerGas': 819, 'maxFeePerGas': 579591921, 'gas': 116372, 'nonce': 2496, 'chainId': 1}
    # tx = {"chainId": 1, "data": "0x095ea7b30000000000000000000000003225737a9bbb6473cb4a45b7244aca2befdb276a000000000000000000000000000000000000000000000000000000000001d4c0", "from": "0x2A804F0c969a4d5c35E551B690Db28371f833567", "gas": 56361, "to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "value": 0, "nonce": 26, "maxFeePerGas": 1640891266, "maxPriorityFeePerGas": 14}
    # print(sign_and_send_transaction(tx, account, w3, bind_address='0x670C68F7fE704211cAcaDa9199Db8d52335CE165'))
    print(sign_and_send_transaction(tx, account, w3))