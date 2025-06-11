# 本脚本用于在本地Solana节点上mint自定义Token
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from spl.token.instructions import (
    initialize_mint,
    create_associated_token_account,
    mint_to_checked,
    MintToCheckedParams,
    InitializeMintParams
)
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from solders.system_program import create_account, CreateAccountParams
import json
import os
from solana.rpc.commitment import Confirmed, Finalized
from solana.rpc.types import TxOpts

from script.sol_utils import get_token_balance

def load_keypair():
    # keyfile = os.path.expanduser("~/.config/solana/id.json")
    keyfile = os.path.expanduser("user.json")
    with open(keyfile) as f:
        secret = json.load(f)
    return Keypair.from_bytes(bytes(secret))

def get_associated_token_address(owner: Pubkey, mint: Pubkey) -> Pubkey:
    seeds = [
        bytes(owner),
        bytes(TOKEN_PROGRAM_ID),
        bytes(mint)
    ]
    address, _ = Pubkey.find_program_address(seeds, ASSOCIATED_TOKEN_PROGRAM_ID)
    return address

# ---------- 基础参数 ----------
RPC_URL = "http://127.0.0.1:12345"
MINT_ADDRESS = Pubkey.from_string("BzEibmtstdW1VyhQQ4TPusLT77V8nPq12RmTnm1x5yPf")  # TRUMP mint
DECIMALS = 6
RECEIVER = load_keypair().pubkey()  # mint给自己

client = Client(RPC_URL)
payer = load_keypair()  # Mint Authority + 付手续费

# 创建新的mint账户

mint_keypair = Keypair.from_json(open("user.json").read())
mint_pubkey = mint_keypair.pubkey()

# 创建mint账户的指令
create_mint_account_ix = create_account(
    CreateAccountParams(
        from_pubkey=payer.pubkey(),
        to_pubkey=mint_pubkey,
        lamports=client.get_minimum_balance_for_rent_exemption(82).value,  # Mint账户大小
        space=82,
        owner=TOKEN_PROGRAM_ID,
    )
)

# 初始化mint
initialize_mint_ix = initialize_mint(
    params=InitializeMintParams(
        mint=mint_pubkey,
        decimals=6,
        mint_authority=payer.pubkey(),  # 你是mint权限持有者
        freeze_authority=payer.pubkey(),
        program_id=TOKEN_PROGRAM_ID,
    )
)

# 获取接收方ATA地址
receiver_ata = get_associated_token_address(RECEIVER, MINT_ADDRESS)

# 检查ATA是否存在
try:
    ata_info = client.get_account_info(receiver_ata)
    ata_exists = ata_info.value is not None
except:
    ata_exists = False

# ---------- 构建指令 ----------
instructions = [create_mint_account_ix, initialize_mint_ix]

# 如果ATA不存在，先创建
if not ata_exists:
    ix_create_ata = create_associated_token_account(
        payer=payer.pubkey(),
        owner=RECEIVER,
        mint=MINT_ADDRESS,
    )
    instructions.append(ix_create_ata)



# ---------- 发送事务 ----------
# recent_blockhash = client.get_latest_blockhash().value.blockhash
# tx = Transaction.new_with_payer(instructions, payer.pubkey())
# tx.sign([payer, mint_keypair], recent_blockhash)

# try:
#     sig = client.send_transaction(tx, opts=TxOpts(skip_preflight=True, preflight_commitment=Confirmed)).value
#     print("创建测试token成功:", sig)
#     print("新token mint地址:", mint_pubkey)
#     confirmation = client.confirm_transaction(sig, commitment=Finalized)
#     print(confirmation.to_json())
# except Exception as e:
#     print("创建失败:", e)


instructions = []

# 使用mint_pubkey创建新的ATA
new_ata = get_associated_token_address(RECEIVER, mint_pubkey)
try:
    new_ata_info = client.get_account_info(new_ata)
    new_ata_exists = new_ata_info.value is not None
except:
    new_ata_exists = False

if not new_ata_exists:
    ix_create_new_ata = create_associated_token_account(
        payer=payer.pubkey(),
        owner=RECEIVER,
        mint=mint_pubkey,
    )
    instructions.append(ix_create_new_ata)


# ---------- 铸币 1000 枚 TRUMP ----------
amount = 1000 * 10**DECIMALS  # 原子量
ix_mint = mint_to_checked(
    params=MintToCheckedParams(
        mint=mint_pubkey,
        dest=new_ata,
        mint_authority=payer.pubkey(),
        amount=amount,
        decimals=DECIMALS,
        program_id=TOKEN_PROGRAM_ID,
    )
)

instructions.append(ix_mint)
recent_blockhash = client.get_latest_blockhash().value.blockhash
tx = Transaction.new_with_payer(instructions, payer.pubkey())
tx.sign([payer], recent_blockhash)
print(get_token_balance(new_ata, client))
try:
    sig = client.send_transaction(tx, opts=TxOpts(skip_preflight=True, preflight_commitment=Confirmed)).value
    print("铸币成功:", sig)
    confirmation = client.confirm_transaction(sig, commitment=Finalized)
    print(confirmation.to_json())
except Exception as e:
    print("铸币失败:", e)


print(get_token_balance(new_ata, client))