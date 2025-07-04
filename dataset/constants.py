import json, os
from pathlib import Path

RPC_URL = "http://127.0.0.1:8545"
BASE_RPC_URL = "http://127.0.0.1:8546"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" 
ACCOUNT_ADDRESS = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
USDT_CONTRACT_ADDRESS_ETH  = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
USDC_CONTRACT_ADDRESS_ETH = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
WETH_CONTRACT_ADDRESS_ETH = "0xC02aaA39b223FE8D0A0E5C4F27eAD9083C756Cc2"
BNB_CONTRACT_ADDRESS_ETH = "0xB8c77482e45F1F44dE1745F52C74426C631bDD52"
LIDO_CONTRACT_ADDRESS_ETH = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"
STETH_CONTRACT_ADDRESS_ETH = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"
WSTETH_CONTRACT_ADDRESS_ETH = "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0"
PEPE_CONTRACT_ADDRESS_ETH="0x6982508145454Ce325dDbE47a25d4ec3d2311933"
SHIB_CONTRACT_ADDRESS_ETH="0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE"

UNISWAP_V2_ROUTER_ADDRESS_ETH = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
UNISWAP_V2_POOL_ADDRESS_WETH_PEPE = "0x0bfbcf9fa4f9c56b0cc798c395a75d9d4c79dd93"
UNISWAP_V2_POOL_ADDRESS_ETH_PEPE = "0xA43fe16908251ee70EF74718545e4FE6C5cCEc9f"

UNISWAP_V3_ROUTER_ADDRESS_ETH = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
UNISWAP_V3_ROUTER_2_ADDRESS_ETH = "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
UNISWAP_V3_POOL_ADDRESS_WETH_USDC = "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640"

UNISWAP_NPM_ADDRESS_ETH = "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"

AAVE_POOL_ADDRESS_ETH = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"

UNISWAP_V4_ROUTER_ADDRESS_ETH='0x66a9893cc07d91d95644aedd05d03f95e1dba8af'
UNISWAP_V4_QUETOR_ADDRESS_ETH='0x52f0e24d1c21c8a0cb1e5a5dd6198556bd9e1203'

UNISWAP_V4_POOL_ADDRESS_WETH_USDC = "0x21c67e77068de97969ba93d4aab21826d33ca12bb9f565d8496e8fda8a82ca27"


ACROSS_PROTOCOL_ADDRESS_ETH = "0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5"
ACROSS_PROTOCOL_HUBPOOL_ADDRESS_ETH = "0xc186fA914353c44b2E33eBE05f21846F1048bEda"

PENDLE_MARKET_ADDRESS="0x4339ffe2b7592dc783ed13cce310531ab366deac"
PENDLE_PT_ADDRESS="0x3b3fb9c57858ef816833dc91565efcd85d96f634"
PENDLE_YT_ADDRESS="0xb7e51d15161c49c823f3951d579ded61cd27272b"

PENDLE_PT_SUSDE_ADDRESS="0x9f56094c450763769ba0ea9fe2876070c0fd5f77"
PENDLE_PT_SUSDE_YT_ADDRESS="0x029d6247adb0a57138c62e3019c92d3dfc9c1840"

PENDLE_ZAP_IN_ADDRESS="0x9df192d13d61609d1852461c4850595e1f56e714"
PENDLE_EUSDE_PT_ADDRESS="0x917459337caac939d41d7493b3999f571d20d667"
PENDLE_EUSDE_YT_ADDRESS="0x733ee9ba88f16023146ebc965b7a1da18a322464"

# Sky.money / MakerDAO related addresses
USDS_CONTRACT_ADDRESS_ETH = "0xdC035D45d973E3EC169d2276DDab16f1e407384F"
SUSDS_CONTRACT_ADDRESS_ETH = "0xa3931d71877c0e7a3148cb7eb4463524fec27fbd"

# ERC20 ABI
# 获取当前文件所在目录
current_dir = Path(__file__).parent
abi_dir = current_dir.parent / "abi"

with open(abi_dir / 'erc20_abi.json', 'r') as f:
    ERC20_ABI = json.load(f)

with open(abi_dir / 'aave_v3_abi.json', 'r') as f:
    AAVE_V3_POOL_ABI = json.load(f)

with open(abi_dir / 'ens_register_controller_abi.json', 'r') as f:
    ENS_REGISTER_CONTROLLER_ABI = json.load(f)

with open(abi_dir / "morpho_abi.json", 'r') as f:
    MORPHO_CONTRACT_ABI = json.load(f)

WETH_CONTRACT_ADDRESS_BASE='0x4200000000000000000000000000000000000006'


MORPHO_CONTRACT_ADDRESS_ETH='0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb'
MORPHO_GENERAL_ADAPTER_ADDRESS_ETH="0x4A6c312ec70E8747a587EE860a0353cd42Be0aE0"
MORPHO_STEAKHOUSE_USDC_VAULT_ADDRESS_ETH='0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB'

ENS_REGISTER_CONTROLLER_ADDRESS_ETH = "0x253553366Da8546fC250F225fe3d25d0C782303b"
ENS_WRAPPER_ADDRESS_ETH = "0xD4416b13d2b3a9aBae7AcD5D6C2BbDBE25686401"


with open(abi_dir / "morpho_vault_abi.json", "r") as f:
    MORPHO_VAULT_ABI = json.load(f)


SUSDE_CONTRACT_ADDRESS_ETH = "0x9D39A5DE30e57443BfF2A8307A4256c8797A3497"
SKY_CONTRACT_ADDRESS_ETH="0x3225737a9Bbb6473CB4a45b7244ACa2BeFdB276A"
USDS_WRAPPER_ADDRESS_ETH ="0xA188EEC8F81263234dA3622A406892F3D630f98c"
PENDLE_ROUTER_V4_ADDRESS_ETH="0x888888888889758F76e7103c6CbF23ABbF58F946"
SUSDS_PROXY_CONTRACT_ADDRESS_ETH="0xa3931d71877C0E7a3148CB7Eb4463524FEc27fbD"

with open(abi_dir / "usds_pm_wrapper_abi.json", "r") as f:
    USDS_PM_WRAPPER_ABI = json.load(f)

with open(abi_dir / "susds_abi.json", "r") as f:
    SUSDS_PROXY_ABI= json.load(f)


USDC_CONTRACT_ADDRESS_BASE="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
BIND_ADDRESS = "0x670C68F7fE704211cAcaDa9199Db8d52335CE165"