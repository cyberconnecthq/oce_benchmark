# 本脚本用于在本地Solana节点（127.0.0.1:8899）上将10 SOL兑换为TRUMP代币
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.system_program import transfer, TransferParams
from solders.instruction import Instruction, AccountMeta
import base64
import yaml
import os
import json
from solders.message import Message
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
# from raydium_py.client import RaydiumClient
# Token程序常量
# TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
# ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
SYSTEM_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111112")

def get_associated_token_address(owner: Pubkey, mint: Pubkey) -> Pubkey:
    """获取关联token账户地址"""
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

def create_transfer_checked_instruction(
    source: Pubkey,
    mint: Pubkey,
    dest: Pubkey,
    owner: Pubkey,
    amount: int,
    decimals: int
) -> Instruction:
    """创建token转账指令"""
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

# 读取配置文件，获取助记词和mint地址
with open("envs/solana/manifest.yaml", "r") as f:
    cfg = yaml.safe_load(f)
SOL_MINT = "So11111111111111111111111111111111111111112"
TRUMP_MINT = "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN"
MNEMONIC = cfg["mnemonic"]

def load_keypair():
    # 优先尝试从本地文件加载
    keyfile = os.path.expanduser("~/.config/solana/id.json")
    if os.path.exists(keyfile):
        with open(keyfile) as f:
            secret = json.load(f)
        return Keypair.from_bytes(bytes(secret))
    # 否则用助记词恢复（这里略，需用bip39和solana_mnemonic库）
    raise Exception("请先生成Solana钱包密钥文件~/.config/solana/id.json")

keypair = load_keypair()
owner = keypair.pubkey()

client = Client("http://127.0.0.1:12345")  # 修正端口

# 查询TRUMP的mint和你的ATA
trump_mint = Pubkey.from_string(TRUMP_MINT)
trump_ata = get_associated_token_address(owner, trump_mint)

# 检查ATA是否存在，不存在则创建
try:
    ata_info = client.get_account_info(trump_ata)
    ata_exists = ata_info.value is not None
except:
    ata_exists = False

instructions = []

if not ata_exists:
    instructions.append(
        create_associated_token_account_instruction(
            payer=owner,
            owner=owner,
            mint=trump_mint
        )
    )


POOL_PUBKEY = Pubkey.from_string("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8") 
instructions.append(
    transfer(
        TransferParams(
            from_pubkey=owner,
            to_pubkey=POOL_PUBKEY,
            lamports=int(10 * 1e9)
        )
    )
)

# 2. 池子给你发TRUMP（这里直接mint，实际应由池子合约完成）
# 这里仅演示如何转账TRUMP（假设池子有TRUMP余额且为池子ATA）
POOL_TRUMP_ATA = get_associated_token_address(POOL_PUBKEY, trump_mint)
instructions.append(
    create_transfer_checked_instruction(
        source=POOL_TRUMP_ATA,
        mint=trump_mint,
        dest=trump_ata,
        owner=POOL_PUBKEY,
        amount=int(10 * 1e6),  # 假设TRUMP精度为6
        decimals=6
    )
)
recent_blockhash = client.get_latest_blockhash().value.blockhash
message = Message.new_with_blockhash(instructions, owner, recent_blockhash)
# 创建交易并添加指令
tx = Transaction.new_unsigned(message)

# 签名并发送交易
try:
    resp = client.simulate_transaction(tx, sig_verify=False)
    print(json.dumps(json.loads(resp.to_json()), indent=4))
    print("交易已发送，签名:", resp.value)
except Exception as e:
    print("交易失败:", e)
