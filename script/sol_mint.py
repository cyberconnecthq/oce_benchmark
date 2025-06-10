# 本脚本用于在本地Solana节点上mint自定义Token
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.message import Message
import json
import os
from spl.token.constants import TOKEN_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
SYSTEM_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111112")
# 加载mint账户密钥对
def load_keypair(path=None):
    if path is None:
        keyfile = os.path.expanduser("~/.config/solana/id.json")
    else:
        keyfile = path
    if os.path.exists(keyfile):
        with open(keyfile) as f:
            secret = json.load(f)
        return Keypair.from_bytes(bytes(secret))
    raise Exception("请先生成Solana钱包密钥文件~/.config/solana/id.json")

# 设置节点和mint地址
client = Client("http://127.0.0.1:12345")
mint_authority = load_keypair()
mint_authority_pub = mint_authority.pubkey()

# 请将下面的mint地址替换为你的token mint地址
MINT_ADDRESS = "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN"  # 示例
mint_pub = Pubkey.from_string(MINT_ADDRESS)

# 目标ATA地址（接收mint的token账户）
def get_associated_token_address(owner: Pubkey, mint: Pubkey) -> Pubkey:
    seeds = [
        bytes(owner),
        bytes(TOKEN_PROGRAM_ID),
        bytes(mint)
    ]
    address, _ = Pubkey.find_program_address(seeds, ASSOCIATED_TOKEN_PROGRAM_ID)
    return address

receiver_pub = mint_authority_pub  # 这里默认mint到自己
receiver_ata = get_associated_token_address(receiver_pub, mint_pub)

# 构造mint_to指令
def create_mint_to_instruction(mint, dest, authority, amount, decimals):
    # MintTo指令数据：指令ID(7) + amount(8字节)
    data = bytes([7]) + amount.to_bytes(8, 'little')
    return Instruction(
        program_id=TOKEN_PROGRAM_ID,
        accounts=[
            AccountMeta(pubkey=mint, is_signer=False, is_writable=True),
            AccountMeta(pubkey=dest, is_signer=False, is_writable=True),
            AccountMeta(pubkey=authority, is_signer=True, is_writable=False),
        ],
        data=data
    )

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
# mint数量和精度
mint_amount = int(1000 * 1e6)  # 1000个token，假设精度为6
decimals = 6

# 检查ATA是否存在，不存在则报错
ata_info = client.get_account_info(receiver_ata)
if ata_info.value is None:
    # raise Exception("目标ATA账户不存在，请先创建ATA账户")
    create_instructions = create_associated_token_account_instruction(
        payer=mint_authority_pub,
        owner=mint_authority_pub,
        mint=mint_pub
    )

mint_to_ix = create_mint_to_instruction(
    mint=mint_pub,
    dest=receiver_ata,
    authority=mint_authority_pub,
    amount=mint_amount,
    decimals=decimals
)

recent_blockhash = client.get_latest_blockhash().value.blockhash
message = Message.new_with_blockhash([create_instructions, mint_to_ix], mint_authority_pub, recent_blockhash)
tx = Transaction.new_unsigned(message)
tx.sign([mint_authority], recent_blockhash)

# 发送交易
try:
    resp = client.send_transaction(tx)
    print("mint交易已发送，签名:", resp.value)
    print(resp.to_json())
except Exception as e:
    print("mint交易失败:", e)
