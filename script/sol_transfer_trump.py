# 本脚本用于将TRUMP代币转账到指定账户
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.message import Message
from solders.instruction import Instruction, AccountMeta
import json
import os
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from solders.system_program import transfer, TransferParams
from solana.rpc.commitment import Confirmed, Finalized
from solana.rpc.types import TxOpts
SYSTEM_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111112")

# 加载发送方密钥对
def load_keypair():
    keyfile = os.path.expanduser("~/.config/solana/id.json")
    if os.path.exists(keyfile):
        with open(keyfile) as f:
            secret = json.load(f)
        return Keypair.from_bytes(bytes(secret))
    raise Exception("请先生成Solana钱包密钥文件~/.config/solana/id.json")

# 获取关联token账户地址
def get_associated_token_address(owner: Pubkey, mint: Pubkey) -> Pubkey:
    seeds = [
        bytes(owner),
        bytes(TOKEN_PROGRAM_ID),
        bytes(mint)
    ]
    address, _ = Pubkey.find_program_address(seeds, ASSOCIATED_TOKEN_PROGRAM_ID)
    return address

# 创建token转账指令（TransferChecked）
def create_transfer_checked_instruction(
    source: Pubkey,
    mint: Pubkey,
    dest: Pubkey,
    owner: Pubkey,
    amount: int,
    decimals: int
) -> Instruction:
    # TransferChecked指令数据：指令ID(12) + amount(8字节) + decimals(1字节)
    data = bytes([12]) + amount.to_bytes(8, 'little') + decimals.to_bytes(1, 'little')
    return Instruction(
        program_id=TOKEN_PROGRAM_ID,
        accounts=[
            AccountMeta(pubkey=source, is_signer=False, is_writable=True),
            AccountMeta(pubkey=mint, is_signer=False, is_writable=False),
            AccountMeta(pubkey=dest, is_signer=False, is_writable=True),
            AccountMeta(pubkey=owner, is_signer=True, is_writable=False),
        ],
        data=data
    )

# 创建ATA账户指令
def create_associated_token_account_instruction(payer: Pubkey, owner: Pubkey, mint: Pubkey) -> Instruction:
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

# 设置节点和TRUMP mint
client = Client("http://127.0.0.1:12345")
TRUMP_MINT = "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN"
trump_mint = Pubkey.from_string(TRUMP_MINT)
decimals = 6  # TRUMP精度

# 加载发送方
sender = load_keypair()
sender_pub = sender.pubkey()
sender_ata = get_associated_token_address(sender_pub, trump_mint)

# 请将下面的接收地址替换为目标地址
receiver_pub = Pubkey.from_string("5rnVpGpHbmr6LAoEaL4ycHXqykb3BhbZoGmh8L7X5Uv")
receiver_ata = get_associated_token_address(receiver_pub, trump_mint)

# 检查接收方ATA是否存在，不存在则创建
try:
    ata_info = client.get_account_info(receiver_ata)
    ata_exists = ata_info.value is not None
except Exception as e:
    print("查询接收方ATA失败:", e)
    ata_exists = False

instructions = []
if not ata_exists:
    instructions.append(
        create_associated_token_account_instruction(
            payer=sender_pub,
            owner=receiver_pub,
            mint=trump_mint
        )
    )

# 设置转账数量（例如转账10个TRUMP）
amount = int(10 * 1e6)  # TRUMP精度是6，不是9

# 构造TRUMP转账指令
instructions.append(
    create_transfer_checked_instruction(
        source=sender_ata,
        mint=trump_mint,
        dest=receiver_ata,
        owner=sender_pub,
        amount=amount,
        decimals=decimals
    )
)

# 获取最新区块哈希
recent_blockhash = client.get_latest_blockhash().value.blockhash

# 构造交易
message = Message.new_with_blockhash(instructions, sender_pub, recent_blockhash)
tx = Transaction.new_unsigned(message)

# 签名交易
tx.sign([sender], recent_blockhash)

# 发送交易
try:
    resp = client.send_transaction(tx)
    print("TRUMP转账交易已发送，签名:", resp.value)
    print(json.dumps(json.loads(resp.to_json()), indent=4))
except Exception as e:
    print("TRUMP转账交易失败:", e)
