
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from spl.token.instructions import (
    create_associated_token_account,
    mint_to_checked,
    MintToCheckedParams,
)
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from solana.rpc.commitment import Confirmed, Finalized
from solana.rpc.types import TxOpts

import json
import os

def get_associated_token_address(owner: Pubkey, mint: Pubkey) -> Pubkey:
    seeds = [
        bytes(owner),
        bytes(TOKEN_PROGRAM_ID),
        bytes(mint)
    ]
    address, _ = Pubkey.find_program_address(seeds, ASSOCIATED_TOKEN_PROGRAM_ID)
    return address

def load_keypair_from_json(filepath):
    with open(filepath, "r") as f:
        secret = json.load(f)
    return Keypair.from_bytes(bytes(secret))

def get_sol_balance(pubkey: Pubkey, client: Client):
    res = client.get_balance(pubkey)
    if hasattr(res, "value"):
        return res.value / 1e9  # lamports to SOL
    return 0

def get_token_balance(ata: Pubkey, client: Client):
    try:
        res = client.get_token_account_balance(ata)
        if hasattr(res, "value") and hasattr(res.value, "amount"):
            return int(res.value.amount)
    except Exception:
        pass
    return 0

def get_token_decimals(mint_pubkey: Pubkey, client: Client):
    try:
        res = client.get_token_supply(mint_pubkey)
        if hasattr(res, "value") and hasattr(res.value, "decimals"):
            return res.value.decimals
    except Exception:
        pass
    return 6  # 默认6位

def mint_100_token_to_account(mint_address: str, account_json_path: str, rpc_url="http://127.0.0.1:12345"):
    """
    mint_address: token的mint地址（字符串）
    account_json_path: 目标账户的keypair json文件路径
    rpc_url: Solana节点RPC地址
    """
    client = Client(rpc_url)
    payer = load_keypair_from_json(account_json_path)
    mint_pubkey = Pubkey.from_string(mint_address)
    mint_keypair = load_keypair_from_json("fake_spl_token.json")
    receiver = payer.pubkey()
    decimals = get_token_decimals(mint_pubkey, client)

    # 获取ATA
    ata = get_associated_token_address(receiver, mint_pubkey)
    try:
        ata_info = client.get_account_info(ata)
        ata_exists = ata_info.value is not None
    except:
        ata_exists = False

    sol_before = get_sol_balance(receiver, client)
    token_before = get_token_balance(ata, client)
    print(f"mint前: SOL余额={sol_before}, SPL Token余额={token_before/(10**decimals)}")

    instructions = []
    if not ata_exists:
        ix_create_ata = create_associated_token_account(
            payer=receiver,
            owner=receiver,
            mint=mint_pubkey,
        )
        instructions.append(ix_create_ata)

    amount = 100 * 10**decimals
    ix_mint = mint_to_checked(
        params=MintToCheckedParams(
            mint=mint_pubkey,
            dest=ata,
            mint_authority=mint_pubkey,
            amount=amount,
            decimals=decimals,
            program_id=TOKEN_PROGRAM_ID,
        )
    )
    instructions.append(ix_mint)

    recent_blockhash = client.get_latest_blockhash().value.blockhash
    tx = Transaction.new_with_payer(instructions, receiver)
    tx.sign([payer, mint_keypair], recent_blockhash)
    try:
        sig = client.send_transaction(tx, opts=TxOpts(skip_preflight=True, preflight_commitment=Confirmed)).value
        print("铸币成功:", sig)
        confirmation = client.confirm_transaction(sig, commitment=Finalized)
        print(confirmation.to_json())
    except Exception as e:
        print("铸币失败:", e)

    sol_after = get_sol_balance(receiver, client)
    token_after = get_token_balance(ata, client)
    print(f"mint后: SOL余额={sol_after}, SPL Token余额={token_after/(10**decimals)}")


if __name__ == "__main__":
    mint_100_token_to_account("BzEibmtstdW1VyhQQ4TPusLT77V8nPq12RmTnm1x5yPf", "user.json")