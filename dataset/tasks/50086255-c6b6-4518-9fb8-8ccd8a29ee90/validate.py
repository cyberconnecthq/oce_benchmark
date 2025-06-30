from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import (
    USDC_CONTRACT_ADDRESS_ETH,
    WETH_CONTRACT_ADDRESS_ETH,
    UNISWAP_V3_POOL_ADDRESS_WETH_USDC
)

RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" #the first default anvil account
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

USDC = Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH)
WETH = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH)
POOL = Web3.to_checksum_address(UNISWAP_V3_POOL_ADDRESS_WETH_USDC)
NPM = Web3.to_checksum_address("0xC36442b4a4522E871399CD717aBDD847Ab11FE88")  # NonfungiblePositionManager

# ERC20 ABI
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

# ERC721 ABI for NFT balance
ERC721_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}, {"name": "_index", "type": "uint256"}],
        "name": "tokenOfOwnerByIndex",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "positions",
        "outputs": [
            {"name": "nonce", "type": "uint96"},
            {"name": "operator", "type": "address"},
            {"name": "token0", "type": "address"},
            {"name": "token1", "type": "address"},
            {"name": "fee", "type": "uint24"},
            {"name": "tickLower", "type": "int24"},
            {"name": "tickUpper", "type": "int24"},
            {"name": "liquidity", "type": "uint128"},
            {"name": "feeGrowthInside0LastX128", "type": "uint256"},
            {"name": "feeGrowthInside1LastX128", "type": "uint256"},
            {"name": "tokensOwed0", "type": "uint128"},
            {"name": "tokensOwed1", "type": "uint128"}
        ],
        "type": "function"
    }
]

usdc_contract = w3.eth.contract(address=USDC, abi=ERC20_ABI)
weth_contract = w3.eth.contract(address=WETH, abi=ERC20_ABI)
pool_contract = w3.eth.contract(address=POOL, abi=ERC20_ABI)
npm_contract = w3.eth.contract(address=NPM, abi=ERC721_ABI)

async def get_nft_positions():
    """Get user's NFT liquidity position information"""
    try:
        # Get number of NFTs owned by user
        nft_balance = npm_contract.functions.balanceOf(addr).call()
        
        if nft_balance == 0:
            return "No NFT liquidity positions"
        
        positions_info = []
        for i in range(nft_balance):
            # Get token ID of the i-th NFT
            token_id = npm_contract.functions.tokenOfOwnerByIndex(addr, i).call()
            
            # Get position info for this NFT
            position = npm_contract.functions.positions(token_id).call()
            
            # Parse position info
            nonce, operator, token0, token1, fee, tick_lower, tick_upper, liquidity, fee_growth_0, fee_growth_1, tokens_owed_0, tokens_owed_1 = position
            
            # Check if this is a WETH/USDC pool
            if (token0.lower() == USDC.lower() and token1.lower() == WETH.lower()) or \
               (token0.lower() == WETH.lower() and token1.lower() == USDC.lower()):
                positions_info.append({
                    'token_id': token_id,
                    'liquidity': liquidity,
                    'fee_tier': fee,
                    'tick_range': f"{tick_lower} → {tick_upper}",
                    'tokens_owed_0': tokens_owed_0,
                    'tokens_owed_1': tokens_owed_1,
                    'fee_growth_0': fee_growth_0,
                    'fee_growth_1': fee_growth_1
                })
        
        if not positions_info:
            return "No WETH/USDC liquidity positions"
        
        result = f"NFT Liquidity Positions ({len(positions_info)}):\n"
        for pos in positions_info:
            result += f"  Token ID: {pos['token_id']}\n"
            result += f"  Liquidity: {pos['liquidity']}\n"
            result += f"  Fee Rate: {pos['fee_tier']/10000}%\n"
            result += f"  Tick Range: {pos['tick_range']}\n"
            result += f"  Uncollected Fees: {pos['tokens_owed_0']/1e6:.6f} USDC, {pos['tokens_owed_1']/1e18:.6f} WETH\n"
            result += f"  feeGrowthInside0LastX128: {pos['fee_growth_0']}\n"
            result += f"  feeGrowthInside1LastX128: {pos['fee_growth_1']}\n"
            result += "  ---\n"
        
        return result
        
    except Exception as e:
        return f"Failed to get NFT position info: {str(e)}"

async def get_balances():
    eth_balance = w3.eth.get_balance(addr)
    # Get USDC balance
    usdc_balance = usdc_contract.functions.balanceOf(addr).call()
    # Get WETH balance
    weth_balance = weth_contract.functions.balanceOf(addr).call()
    # Get pool balances
    pool_weth_balance = weth_contract.functions.balanceOf(POOL).call()
    pool_usdc_balance = usdc_contract.functions.balanceOf(POOL).call()
    
    # Get NFT position info
    nft_positions = await get_nft_positions()
    
    return (
        f"Current Wallet Balances:\n"
        f"{eth_balance / 10**18:.6f} ETH\n"
        f"{usdc_balance / 10**6:.6f} USDC\n"
        f"{weth_balance / 10**18:.6f} WETH\n"
        f"Pool WETH: {pool_weth_balance / 10**18:.6f} WETH\n"
        f"Pool USDC: {pool_usdc_balance / 10**6:.6f} USDC\n\n"
        f"{nft_positions}"
    )

if __name__ == '__main__':
    import asyncio
    print(asyncio.run(get_balances()))
