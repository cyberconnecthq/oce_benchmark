from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import USDC_CONTRACT_ADDRESS_ETH, USDS_CONTRACT_ADDRESS_ETH, RPC_URL, PRIVATE_KEY, SUSDS_CONTRACT_ADDRESS_ETH

# 初始化web3和账户
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

USDC = Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH)
USDS = Web3.to_checksum_address(USDS_CONTRACT_ADDRESS_ETH)
SUSDS = Web3.to_checksum_address(SUSDS_CONTRACT_ADDRESS_ETH)

# ERC20 ABI（balanceOf）
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

# 获取合约实例
usdc_contract = w3.eth.contract(address=USDC, abi=ERC20_ABI)
usds_contract = w3.eth.contract(address=USDS, abi=ERC20_ABI)
susds_contract = w3.eth.contract(address=SUSDS, abi=ERC20_ABI)

def get_usdc_usds_balances():
    usdc_balance = usdc_contract.functions.balanceOf(addr).call()
    usds_balance = usds_contract.functions.balanceOf(addr).call()
    susds_balance = susds_contract.functions.balanceOf(addr).call()
    return (
        f"USDC余额: {usdc_balance / 10**6:.6f} USDC\n"
        f"USDS余额: {usds_balance / 10**18:.6f} USDS\n"
        f"SUSDS余额: {susds_balance / 10**18:.6f} SUSDS"
    )

if __name__ == "__main__":
    print(get_usdc_usds_balances())
