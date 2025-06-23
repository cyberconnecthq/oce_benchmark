from web3 import HTTPProvider, Web3
from dataset.constants import PRIVATE_KEY, RPC_URL
from datetime import datetime, timezone
from eth_utils.crypto import keccak
from eth_utils.address import to_checksum_address
from eth_account.signers.local import LocalAccount

w3 = Web3(HTTPProvider(RPC_URL))
account: LocalAccount = w3.eth.account.from_key(PRIVATE_KEY)

def namehash(name: str) -> bytes:
    """
    EIP-137 namehash implementation (no ENS lib dependency)
    """
    node = b"\x00" * 32  # hash of the empty string
    if name:
        for label in name.lower().split(".")[::-1]:
            label_hash = Web3.keccak(text=label)
            node = Web3.keccak(node + label_hash)
    return node

ENS_REGISTRY = "0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e"   # mainnet
NAME = "caiba-ai.eth"
NAMEHASH = namehash(name=NAME)                  # EIP-137 namehash
TOKEN_ID = int.from_bytes(NAMEHASH, "big")

NAMEWRAPPER = Web3.to_checksum_address(
    "0xD4416b13d2b3a9aBae7AcD5D6C2BbDBE25686401"
)
wrapper = w3.eth.contract(
    address=NAMEWRAPPER,
    abi=[{
        "name": "balanceOf",
        "inputs": [{"name": "account", "type": "address"}, {"name": "id", "type": "uint256"}],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }]
)

# BaseRegistrarImplementation (mainnet)
BASE_REGISTRAR = to_checksum_address("0x57f1887a8BF19b14fC0dF6Fd9B2acc9Af147eA85")
# Simplified ABI: only keep nameExpires()
REGISTRAR_ABI = [{
    "name": "nameExpires",
    "inputs": [{"name": "id", "type": "uint256"}],
    "outputs": [{"name": "", "type": "uint256"}],
    "stateMutability": "view",
    "type": "function"
}]
registrar = w3.eth.contract(address=BASE_REGISTRAR, abi=REGISTRAR_ABI)

def get_balances():
    target_add = "0xcCb30F16d38424F7a546944F0cf5EF8F2d116F70"
    wens_balance = wrapper.functions.balanceOf(Web3.to_checksum_address(target_add), TOKEN_ID).call()

    # Query expiration time
    label = NAME.lower().split(".")[0]
    label_hash = int.from_bytes(keccak(text=label), "big")
    ts_expire = registrar.functions.nameExpires(label_hash).call()
    if ts_expire == 0:
        expire_info = f"❌  {NAME} is not registered or has expired"
    else:
        # Use the latest block's timestamp as the current time
        latest_block = w3.eth.get_block('latest')
        now_ts = latest_block['timestamp']
        dt_expire = datetime.fromtimestamp(ts_expire, tz=timezone.utc)
        dt_now = datetime.fromtimestamp(now_ts, tz=timezone.utc)
        remaining = dt_expire - dt_now
        expire_info = (
            f"✅  {NAME} expiration time: {dt_expire.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
            f"    (Remaining {remaining.days} days {remaining.seconds // 3600} hours)"
        )

    return (
        f"Balance of address {target_add}:\n\n"
        f"wENS balance: {wens_balance} wENS\n"
        f"{expire_info}"
    )

if __name__ == '__main__':
    print(get_balances())