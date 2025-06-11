from solana.rpc.api import Client
from solders.pubkey import Pubkey
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
from solana.rpc.commitment import Confirmed
SYSTEM_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111111")

def get_solana_balance(pubkey:Pubkey, client:Client) -> float:
    try:
        balance_resp = client.get_balance(pubkey, commitment=Confirmed)
        balance = balance_resp.value / 1e6
        return balance
    except Exception as e:
        print("查询余额失败:", e)
        return False

def get_token_balance(pubkey:Pubkey, client:Client) -> float:
    try:
        balance_resp = client.get_token_account_balance(pubkey, commitment=Confirmed)
        balance = balance_resp.value.ui_amount
        return balance if balance is not None else 0
    except Exception as e:
        print("查询余额失败:", e)
        return False

# 目标ATA地址（接收mint的token账户）
def get_associated_token_address(owner: Pubkey, mint: Pubkey) -> Pubkey:
    seeds = [
        bytes(owner),
        bytes(TOKEN_PROGRAM_ID),
        bytes(mint)
    ]
    address, _ = Pubkey.find_program_address(seeds, ASSOCIATED_TOKEN_PROGRAM_ID)
    return address

def create_associated_token_account_instruction(payer: Pubkey, owner: Pubkey, mint: Pubkey) -> Instruction:
    """创建关联token账户指令"""
    ata = get_associated_token_address(owner, mint)
    
    return Instruction(
        program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
        accounts=[
            AccountMeta(pubkey=payer, is_signer=True, is_writable=True),
            AccountMeta(pubkey=ata, is_signer=False, is_writable=True),
            AccountMeta(pubkey=owner, is_signer=False, is_writable=False),
            AccountMeta(pubkey=mint, is_signer=False, is_writable=False),
            AccountMeta(pubkey=SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=Pubkey.from_string("SysvarRent111111111111111111111111111111111"), is_signer=False, is_writable=False),
        ],
        data=bytes()
    )

if __name__ == "__main__":
    client = Client("http://127.0.0.1:12345")
    pubkey = Pubkey.from_string("9SLPTL41SPsYkgdsMzdfJsxymEANKr5bYoBsQzJyKpKS")
    ata = get_associated_token_address(pubkey, Pubkey.from_string("9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump"))
    print(ata)
    print(get_token_balance(ata, client))
    print(get_solana_balance(pubkey, client))