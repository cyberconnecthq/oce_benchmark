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
    tx = {'to': '0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb', 'value': 0, 'data': '0x238d6579000000000000000000000000dac17f958d2ee523a2206206994597c13d831ec7000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000e9ee579684716c7bb837224f4c7beefa4f1f3d7f000000000000000000000000870ac11d48b15db9a138cf899d20f13f79ba00bc0000000000000000000000000000000000000000000000000cb2bba6f17b800000000000000000000000000000000000000000000000000000038d7ea4c680000000000000000000000000002a804f0c969a4d5c35e551b690db28371f83356700000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000', 'nonce': 2493, 'chainId': 1, 'from': '0x2A804F0c969a4d5c35E551B690Db28371f833567', 'gasPrice': 3000000000, 'gas': 8000000}
    print(sign_and_send_transaction(tx, account, w3))