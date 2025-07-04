from dataset.constants import USDS_CONTRACT_ADDRESS_ETH, RPC_URL, PRIVATE_KEY, USDC_CONTRACT_ADDRESS_ETH
from web3 import Web3, HTTPProvider

# 假设本地RPC和账户私钥
w3 = Web3(HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

# ERC20 ABI（只需balanceOf）
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH), abi=ERC20_ABI)
usds = w3.eth.contract(address=Web3.to_checksum_address(USDS_CONTRACT_ADDRESS_ETH), abi=ERC20_ABI)

async def get_balances():
    usdc_balance = usdc.functions.balanceOf(addr).call()
    usds_balance = usds.functions.balanceOf(addr).call()
    return (
        f"当前钱包地址: {addr}\n"
        f"USDC余额: {usdc_balance / 1e6:.6f} USDC\n"
        f"USDS余额: {usds_balance / 1e18:.6f} USDS"
    )

if __name__ == "__main__":
    import asyncio
    print(asyncio.run(get_balances()))