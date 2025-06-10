from web3 import Web3, HTTPProvider

w3 = Web3(HTTPProvider("http://127.0.0.1:8545"))
addr = w3.to_checksum_address("0xFAafe5FcaC0E87D40017E44CD462398026a12230")     # 你想要的测试账户
print(f"目标地址: {addr}")
target_bal = w3.to_wei(500, "ether")

# ❷ 设置余额
w3.provider.make_request(
    "anvil_setBalance",
    [addr, hex(target_bal)]
)

# 向指定地址转账10 ETH
from_address = w3.eth.accounts[0]  # 默认第一个账户作为发送方
print(f"发送方地址: {from_address}")
from_balance = w3.eth.get_balance(from_address)
print(f"发送方余额: {w3.from_wei(from_balance, 'ether')} ETH")
to_address = w3.eth.accounts[1]
print(f"目标地址: {to_address}")
value = w3.to_wei(10, "ether")
print(f"转账金额: {w3.from_wei(value, 'ether')} ETH")
tx_hash = w3.eth.send_transaction({
    "from": from_address,
    "to": to_address,
    "value": value
})
# estimated_gas = w3.eth.estimate_gas({
#     "data": 0xa9059cbb000000000000000000000000a6210ff05a55b03006493507efccdb461cd9409e0000000000000000000000000000000000000000000000000000000110a24fe9
# })
# print(f"估计的gas: {estimated_gas}")

# 等待交易被打包
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"交易哈希: {str(tx_hash)}")
print(f"交易收据: {receipt}")

# 查询目标地址余额
balance = w3.eth.get_balance(to_address)
print(f"{to_address} 的余额为: {w3.from_wei(balance, 'ether')} ETH")
