from web3 import Web3, HTTPProvider
from eth_account.signers.local import LocalAccount
from dataset.constants import (
    USDC_CONTRACT_ADDRESS_ETH,
    WETH_CONTRACT_ADDRESS_ETH,
    UNISWAP_V3_POOL_ADDRESS_WETH_USDC
)
import math

RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"  # the first default anvil account
w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address

USDC = Web3.to_checksum_address(USDC_CONTRACT_ADDRESS_ETH)
WETH = Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH)
POOL = Web3.to_checksum_address(UNISWAP_V3_POOL_ADDRESS_WETH_USDC)
NPM = Web3.to_checksum_address("0xC36442b4a4522E871399CD717aBDD847Ab11FE88")  # NonfungiblePositionManager

target_address = Web3.to_checksum_address("0xD117Bd6dE83e3F14265a3CE2BEEE6bd69d29eC7E")
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

# Pool ABI for getting current price
POOL_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"name": "sqrtPriceX96", "type": "uint160"},
            {"name": "tick", "type": "int24"},
            {"name": "observationIndex", "type": "uint16"},
            {"name": "observationCardinality", "type": "uint16"},
            {"name": "observationCardinalityNext", "type": "uint16"},
            {"name": "feeProtocol", "type": "uint8"},
            {"name": "unlocked", "type": "bool"}
        ],
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
pool_contract = w3.eth.contract(address=POOL, abi=POOL_ABI)
npm_contract = w3.eth.contract(address=NPM, abi=ERC721_ABI)

def calculate_position_amounts(liquidity, sqrtPriceX96, tick_lower, tick_upper, current_tick):
    """
    Calculate the actual token amounts in the position.

    Args:
        liquidity: The liquidity amount
        sqrtPriceX96: The current sqrt price * 2^96
        tick_lower: Lower tick
        tick_upper: Upper tick
        current_tick: Current tick

    Returns:
        (amount0, amount1): The amounts of token0 and token1
    """
    if liquidity == 0:
        return 0, 0

    # Calculate sqrtPrice for each tick
    sqrtPriceLowerX96 = int((1.0001 ** (tick_lower / 2)) * (2 ** 96))
    sqrtPriceUpperX96 = int((1.0001 ** (tick_upper / 2)) * (2 ** 96))

    if current_tick < tick_lower:
        # Current price is below range, only token0
        amount0 = liquidity * (sqrtPriceUpperX96 - sqrtPriceLowerX96) // (sqrtPriceLowerX96 * sqrtPriceUpperX96 // (2**96))
        amount1 = 0
    elif current_tick >= tick_upper:
        # Current price is above range, only token1
        amount0 = 0
        amount1 = liquidity * (sqrtPriceUpperX96 - sqrtPriceLowerX96) // (2**96)
    else:
        # Current price is within range, both tokens
        amount0 = liquidity * (sqrtPriceUpperX96 - sqrtPriceX96) // (sqrtPriceX96 * sqrtPriceUpperX96 // (2**96))
        amount1 = liquidity * (sqrtPriceX96 - sqrtPriceLowerX96) // (2**96)

    return amount0, amount1

async def get_nft_positions(addr = addr):
    """Get user's NFT liquidity position information"""
    try:
        # Get current pool state
        slot0 = pool_contract.functions.slot0().call()
        sqrtPriceX96, current_tick = slot0[0], slot0[1]

        # Calculate current price
        current_price = (sqrtPriceX96 / (2**96)) ** 2
        usdc_per_weth = 1 / current_price * (10**12)  # Adjust for decimals
        
        # Get number of NFTs owned by user
        nft_balance = npm_contract.functions.balanceOf(addr).call()
        
        if nft_balance == 0:
            return f"No NFT liquidity positions for {addr}\nCurrent Pool Price: {usdc_per_weth:.2f} USDC/WETH"
        
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
                
                # Calculate actual token amounts in the position
                amount0, amount1 = calculate_position_amounts(
                    liquidity, sqrtPriceX96, tick_lower, tick_upper, current_tick
                )
                
                # Determine which is USDC and which is WETH
                if token0.lower() == USDC.lower():
                    usdc_amount = amount0 / 1e6
                    weth_amount = amount1 / 1e18
                else:
                    usdc_amount = amount1 / 1e6
                    weth_amount = amount0 / 1e18
                
                # Calculate tick prices
                tick_lower_price = 1.0001 ** tick_lower * (10**12)
                tick_upper_price = 1.0001 ** tick_upper * (10**12)
                
                positions_info.append({
                    'token_id': token_id,
                    'liquidity': liquidity,
                    'fee_tier': fee,
                    'tick_range': f"{tick_lower} → {tick_upper}",
                    'tick_price_range': f"{tick_lower_price:.0f} → {tick_upper_price:.0f} USDC/WETH",
                    'usdc_amount': usdc_amount,
                    'weth_amount': weth_amount,
                    'tokens_owed_0': tokens_owed_0,
                    'tokens_owed_1': tokens_owed_1,
                    'current_tick': current_tick,
                    'in_range': tick_lower <= current_tick < tick_upper
                })
        
        if not positions_info:
            return f"No WETH/USDC liquidity positions\nCurrent Pool Price: {usdc_per_weth:.2f} USDC/WETH"
        
        result = f"Current Pool Price: {usdc_per_weth:.2f} USDC/WETH (tick: {current_tick})\n\n"
        result += f"NFT Liquidity Positions ({len(positions_info)}) for {addr}:\n"
        
        for pos in positions_info:
            result += f"  Token ID: {pos['token_id']}\n"
            result += f"  Liquidity: {pos['liquidity']:,}\n"
            result += f"  Fee Tier: {pos['fee_tier']/10000}%\n"
            result += f"  Tick Range: {pos['tick_range']}\n"
            result += f"  Price Range: {pos['tick_price_range']}\n"
            result += f"  Status: {'✅ Active' if pos['in_range'] else '❌ Inactive'}\n"
            result += f"  💰 Actual Funds:\n"
            result += f"    USDC: {pos['usdc_amount']:.6f}\n"
            result += f"    WETH: {pos['weth_amount']:.6f}\n"
            result += f"    Estimated Value: ${pos['usdc_amount'] + pos['weth_amount'] * usdc_per_weth:.2f} USD\n"
            result += f"  Uncollected Fees:\n"
            result += f"    Token0: {pos['tokens_owed_0']/1e6:.6f}\n"
            result += f"    Token1: {pos['tokens_owed_1']/1e18:.6f}\n"
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
    nft_positions = await get_nft_positions(addr = target_address)
    
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
