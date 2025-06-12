from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import USDC_CONTRACT_ADDRESS_ETH, WETH_CONTRACT_ADDRESS_ETH, AAVE_POOL_ADDRESS_ETH

RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" #the first default anvil account
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

USDC = Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH)

# ERC20 ABI with allowance function
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

# 获取合约实例
usdc_contract = w3.eth.contract(address=USDC, abi=ERC20_ABI)
weth_contract = w3.eth.contract(address=Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH), abi = ERC20_ABI)

async def get_balances():
    # 检查 addr 对 USDC 合约的授权额度
    allowance = usdc_contract.functions.allowance(addr, USDC).call()
    return (
        f"USDC Allowance for address {addr}:\n"
        f"{allowance / 10**6} USDC\n"
    )


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(get_balances()))