from decimal import Decimal
from web3 import Web3

# ---------- Sky core addresses (Ethereum main-net) ----------
USDS_TOKEN  = Web3.to_checksum_address("0xdC035D45d973E3EC169d2276DDab16f1e407384F")   # USDS token [oai_citation:0‡developers.sky.money](https://developers.sky.money/quick-start/deployments-tracker)
SUSDS_VAULT = Web3.to_checksum_address("0xa3931d71877C0E7a3148CB7Eb4463524FEc27fbD")   # sUSDS ERC-4626 vault [oai_citation:1‡developers.sky.money](https://developers.sky.money/quick-start/deployments-tracker)

# Stables that already have a Lite-PSM wrapper → USDS
TOKEN_WRAPPERS = {
    # token           → wrapper that turns it into USDS
    Web3.to_checksum_address("0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"):  # USDC
        Web3.to_checksum_address("0xA188EEC8F81263234dA3622A406892F3D630f98c"),  # USDS LitePSMWrapper-USDC [oai_citation:2‡developers.sky.money](https://developers.sky.money/quick-start/deployments-tracker)
    Web3.to_checksum_address("0x6b175474e89094c44da98b954eedeac495271d0f"):  # DAI
        Web3.to_checksum_address("0xf6e72Db5454dd049d0788e411b06CfAF16853042"),  # DAI LitePSM-USDC (wrapper calls this) [oai_citation:3‡developers.sky.money](https://developers.sky.money/quick-start/deployments-tracker) [oai_citation:4‡developers.sky.money](https://developers.sky.money/guides/psm/litepsm/)
    # add more token → wrapper pairs as new deployments appear
}

# ---------- minimal ABIs ----------
ERC20_ABI = [
    {"name": "approve",   "type": "function", "inputs":[{"type":"address"},{"type":"uint256"}],"outputs":[{"type":"bool"}]},
    {"name": "decimals",  "type": "function", "stateMutability":"view", "inputs":[],"outputs":[{"type":"uint8"}]},
    {"name": "balanceOf", "type": "function", "stateMutability":"view", "inputs":[{"type":"address"}],"outputs":[{"type":"uint256"}]},
]

WRAPPER_ABI = [
    # sellGem(address usr, uint256 gemAmt) → uint256 usdsOut
    {"name": "sellGem", "type": "function", "inputs":[{"type":"address"},{"type":"uint256"}],
     "outputs":[{"type":"uint256"}]},
]

VAULT_ABI = [
    # deposit(uint256 assets, address receiver) → uint256 shares
    {"name": "deposit", "type":"function", "inputs":[{"type":"uint256"},{"type":"address"}],
     "outputs":[{"type":"uint256"}]},
]

# ---------- the one-liner you call ----------
def deposit_to_sky(w3: Web3,
                   token_addr: str,
                   amount: float,
                   priv_key: str,
                   gas_price_gwei: int = 5) -> str:
    """
    Converts `amount` of `token_addr` to USDS (if needed) and deposits
    the resulting USDS into the sUSDS vault.  Returns the *final* tx-hash.
    """

    acct      = w3.eth.account.from_key(priv_key).address
    token_addr = Web3.to_checksum_address(token_addr)

    def _build(tx):
        tx["from"]     = acct
        tx["chainId"]  = w3.eth.chain_id
        tx["nonce"]    = w3.eth.get_transaction_count(acct)
        tx["gasPrice"] = w3.to_wei(gas_price_gwei, "gwei")
        return tx

    # Handy helpers
    def _sign_send(tx):         # sign + relay, returns hash
        signed = w3.eth.account.sign_transaction(tx, priv_key)
        return w3.eth.send_raw_transaction(signed.raw_transaction)

    # === case 1: caller already holds USDS =========================
    if token_addr == USDS_TOKEN:
        usds  = w3.eth.contract(USDS_TOKEN,  ERC20_ABI)
        vault = w3.eth.contract(SUSDS_VAULT, VAULT_ABI)
        dec   = usds.functions.decimals().call()
        raw   = int(Decimal(str(amount)) * 10**dec)

        # approve + deposit
        _sign_send(usds.functions.approve(SUSDS_VAULT, raw).build_transaction(_build({})))
        final_hash = _sign_send(vault.functions.deposit(raw, acct).build_transaction(_build({})))
        return final_hash.hex()

    # === case 2: we need to wrap first (e.g. USDC, DAI) ============
    if token_addr not in TOKEN_WRAPPERS:
        raise ValueError("No Sky wrapper registered for this token.")

    wrapper_addr = TOKEN_WRAPPERS[token_addr]
    token   = w3.eth.contract(token_addr,  ERC20_ABI)
    wrapper = w3.eth.contract(wrapper_addr, WRAPPER_ABI)
    usds    = w3.eth.contract(USDS_TOKEN,  ERC20_ABI)
    vault   = w3.eth.contract(SUSDS_VAULT, VAULT_ABI)

    dec     = token.functions.decimals().call()
    raw_amt = int(Decimal(str(amount)) * 10**dec)

    # 1️⃣ approve the wrapper to pull the tokens
    _sign_send(token.functions.approve(wrapper_addr, raw_amt).build_transaction(_build({})))

    # 2️⃣ swap → USDS (sellGem)
    swap_hash = _sign_send(wrapper.functions.sellGem(acct, raw_amt).build_transaction(_build({})))
    w3.eth.wait_for_transaction_receipt(swap_hash)

    # 3️⃣ approve USDS to vault and deposit
    usds_raw = usds.functions.balanceOf(acct).call()
    _sign_send(usds.functions.approve(SUSDS_VAULT, usds_raw).build_transaction(_build({})))
    final_hash = _sign_send(vault.functions.deposit(usds_raw, acct).build_transaction(_build({})))
    return final_hash.hex()

if __name__ == '__main__':
    from dataset.constants import RPC_URL, PRIVATE_KEY
    from web3 import Web3, HTTPProvider
    w3 = Web3(HTTPProvider(RPC_URL))
    account = w3.eth.account.from_key(PRIVATE_KEY)
    addr = account.address
    print(deposit_to_sky(w3, USDS_TOKEN, 1, PRIVATE_KEY))