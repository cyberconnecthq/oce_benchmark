from eth_typing import ChecksumAddress
from dataset.constants import (
    MORPHO_CONTRACT_ADDRESS_ETH, 
    RPC_URL, 
    PRIVATE_KEY, 
    ERC20_ABI,
    WETH_CONTRACT_ADDRESS_ETH
)
import json
from web3 import Web3

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
addr = account.address
# 初始化 WETH 合约实例


weth = w3.eth.contract(address=Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH), abi=ERC20_ABI)


def load_morpho_contract(w3: Web3):
    """
    加载 Morpho 合约实例

    参数:
        w3 (Web3): 已连接的 Web3 实例

    返回:
        Contract: Morpho 合约对象
    """
    with open("abi/morpho_abi.json", "r") as f:
        abi = json.load(f)
    contract = w3.eth.contract(address=Web3.to_checksum_address(MORPHO_CONTRACT_ADDRESS_ETH), abi=abi)
    return contract


morpho_contract = load_morpho_contract(w3)

def get_token_balance(token_address, holder_address):
    """
    查询Morpho合约中持有某个ERC20代币的数量

    参数:
        token_address (str): 代币合约地址
        holder_address (str): 持币地址（如Morpho合约地址）

    返回:
        int: 代币余额（单位：最小单位）
    """
    # ERC20 ABI 只需要 balanceOf 方法
    erc20_abi = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }
    ]
    token_contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc20_abi)
    balance = token_contract.functions.balanceOf(Web3.to_checksum_address(holder_address)).call()
    return balance


def approve_weth_to_morpho(amount_wei: int, address: ChecksumAddress):
    allowance = weth.functions.allowance(address, MORPHO_CONTRACT_ADDRESS_ETH).call()
    if allowance < amount_wei:
        tx = weth.functions.approve(MORPHO_CONTRACT_ADDRESS_ETH, amount_wei).build_transaction({
            "from": address,
            "nonce": w3.eth.get_transaction_count(address),
            "gas": 60000,
        })
        signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print("Approved MorphO contract to spend 1 WETH")
    else:
        print("MorphO approval is sufficient")
    

def supply_weth_to_morpho(amount_wei: int, from_address:ChecksumAddress):
    # 需要构造 MarketParams 结构体
    # 这里假设 loanToken=WETH，collateralToken=0x0(无抵押)，oracle/irm/lltv 需根据实际合约配置
    # 这里只做演示，实际参数请根据合约 ABI 和部署情况调整
    # 你需要根据 morpho_abi.json 里的 MarketParams 结构体定义来填写参数
    # 下面是一个示例（参数需根据实际情况填写）
    market_params = (
        Web3.to_checksum_address(WETH_CONTRACT_ADDRESS_ETH),  # loanToken
        "0x0000000000000000000000000000000000000000",         # collateralToken
        "0xbD60A6770b27E084E8617335ddE769241B0e71D8",         # oracle
        "0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC",         # irm
        0                                                     # lltv
    )
    # supply(MarketParams memory marketParams, uint256 assets, uint256 shares, address onBehalf, bytes data)
    tx = morpho_contract.functions.supply(
        market_params,
        amount_wei,    # assets
        0,            # shares (0 表示不限制shares)
        from_address,      # onBehalf
        b''           # data (空字节)
    ).build_transaction({
        "from": from_address,
        "nonce": w3.eth.get_transaction_count(from_address),
        "gas": 300000,
    })
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(receipt.values())
    return receipt['status'] == 1