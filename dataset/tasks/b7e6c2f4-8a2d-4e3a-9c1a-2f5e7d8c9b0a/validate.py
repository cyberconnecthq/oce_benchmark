from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount

# ETH主网RPC和Cyber链RPC（请替换为实际的Cyber链RPC URL）
ETH_RPC_URL = "http://127.0.0.1:8545"
CYBER_RPC_URL = "http://127.0.0.1:8546"  # 假设Cyber链本地8546端口，实际请替换

PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" # 默认anvil账户

# 连接ETH主网
w3_eth = Web3(HTTPProvider(ETH_RPC_URL))
account: LocalAccount = w3_eth.eth.account.from_key(PRIVATE_KEY)
addr = account.address

# 连接Cyber链
w3_cyber = Web3(HTTPProvider(CYBER_RPC_URL))

async def get_eth_and_cyber_balances():
    eth_balance = w3_eth.eth.get_balance(addr)
    cyber_balance = w3_cyber.eth.get_balance(addr)
    return (
        f"地址: {addr}\n"
        f"ETH主网余额: {eth_balance / 10**18} ETH\n"
        f"Cyber链余额: {cyber_balance / 10**18} ETH\n"
    )

if __name__ == '__main__':
    import asyncio
    print(asyncio.run(get_eth_and_cyber_balances()))