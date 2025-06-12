from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount

# ETH主网RPC
ETH_RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"  # 默认anvil账户

# 连接ETH主网
w3 = Web3(HTTPProvider(ETH_RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

# ERC721 ABI（仅balanceOf和tokenOfOwnerByIndex方法）
ERC721_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_index", "type": "uint256"}
        ],
        "name": "tokenOfOwnerByIndex",
        "outputs": [{"name": "tokenId", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "tokenURI",
        "outputs": [{"name": "uri", "type": "string"}],
        "type": "function"
    }
]

# 以ENS NFT合约为例（主网地址）
ENS_NFT_CONTRACT = Web3.to_checksum_address("0x57f1887a8BF19b14fC0dF6Fd9B2acc9Af147eA85")

ens_contract = w3.eth.contract(address=ENS_NFT_CONTRACT, abi=ERC721_ABI)

async def get_eth_and_nft_info():
    eth_balance = w3.eth.get_balance(addr)
    nft_balance = ens_contract.functions.balanceOf(addr).call()
    nft_token_ids = []
    for i in range(nft_balance):
        token_id = ens_contract.functions.tokenOfOwnerByIndex(addr, i).call()
        nft_token_ids.append(token_id)
    return (
        f"地址: {addr}\n"
        f"ETH余额: {eth_balance / 10**18} ETH\n"
        f"ENS NFT持有数量: {nft_balance}\n"
        f"ENS NFT Token IDs: {nft_token_ids}\n"
    )

if __name__ == '__main__':
    import asyncio
    print(asyncio.run(get_eth_and_nft_info()))