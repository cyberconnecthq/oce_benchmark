from dataset.constants import (
    BASE_RPC_URL,
    PRIVATE_KEY,
    WETH_CONTRACT_ADDRESS_BASE
)
from web3 import Web3, HTTPProvider

w3 = Web3(HTTPProvider(BASE_RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

def wrap_eth_to_weth(amount):
    """
    在Base链上将ETH包装成WETH
    :param amount: 需要包装的ETH数量（单位：ETH）
    """
    # WETH合约地址（Base链）
    # WETH ABI（只需deposit方法）
    WETH_ABI = [
        {
            "constant": False,
            "inputs": [],
            "name": "deposit",
            "outputs": [],
            "payable": True,
            "stateMutability": "payable",
            "type": "function"
        }
    ]
    weth = w3.eth.contract(address=Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_BASE), abi=WETH_ABI)
    tx = weth.functions.deposit().build_transaction({
        "from": addr,
        "value": w3.to_wei(amount, "ether"),
        "nonce": w3.eth.get_transaction_count(addr),
        "gas": 100000,
        "gasPrice": w3.to_wei("0.1", "gwei")
    })
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"wrap eth to weth 交易已发送，哈希: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("交易回执:", receipt)
    return receipt



if __name__ == '__main__':
    wrap_eth_to_weth(1)