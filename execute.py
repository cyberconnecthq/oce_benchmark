import os
from web3 import Web3, HTTPProvider
from web3.types import TxParams
from eth_account.signers.local import LocalAccount



def sign_and_send_transaction(tx: TxParams, account:LocalAccount, w3:Web3) -> tuple[bool, int]:
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

    if tx.get('to', "") == "":
        print("Transaction failed! No 'to' address specified.")
        return False, 0

    # Check if gasPrice is in tx
    if "gasPrice" not in tx:
        # If not, use maxFeePerGas and maxPriorityFeePerGas if available, otherwise set a default gasPrice
        if "maxFeePerGas" not in tx and "maxPriorityFeePerGas" not in tx:
            tx['gasPrice'] = w3.to_wei(30, 'gwei')
    if 'gas' not in tx:
        tx['gas'] = 800_000
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
    w3 = Web3(HTTPProvider("http://127.0.0.1:8545"))
    account = w3.eth.account.from_key("0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80")
    tx = {"chainId": 1, "data": "0xb460af94000000000000000000000000000000000000000000000000000000000007a1200000000000000000000000002a804f0c969a4d5c35e551b690db28371f8335670000000000000000000000002a804f0c969a4d5c35e551b690db28371f833567", "from": "0x2A804F0c969a4d5c35E551B690Db28371f833567", "gas": 323209, "to": "0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB", "value": 0, "nonce": 23, "maxFeePerGas": 937832218, "maxPriorityFeePerGas": 100000}
    print(sign_and_send_transaction(tx, account, w3))