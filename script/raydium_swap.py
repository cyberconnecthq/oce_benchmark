import json
import os
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.system_program import TransferParams, transfer
from solders.instruction import Instruction, AccountMeta
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import transfer_checked, TransferCheckedParams
from solders.message import Message
from solana.rpc.commitment import Confirmed, Finalized
from solana.rpc.types import TxOpts
from script.sol_utils import create_associated_token_account_instruction, get_solana_balance, get_token_balance
# 0️⃣ 连接到本地节点
rpc_url = "http://localhost:12345"
client = Client(rpc_url)

# 1️⃣ 关键地址配置 (需预先部署)
RAYDIUM_PROGRAM_ID = Pubkey.from_string("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")  # Raydium AMM 主网ID
USDC_MINT = Pubkey.from_string("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")  # USDC 代币
WSOL_MINT = Pubkey.from_string("So11111111111111111111111111111111111111112")
RAY_MINT = Pubkey.from_string("4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R")  # RAY 代币
POOL_ID = Pubkey.from_string("AVs9TA4nWDzfPJE9gGVNJMVhcQy3V9PGazuz33BfG2RA")  # 流动性池地址

def swap_sol_wsol():
    """
    将SOL兑换为WSOL（即：创建WSOL账户并转入SOL，WSOL即为SPL Token形式的SOL）
    """
    from spl.token.instructions import (
        create_associated_token_account,
    )
    from spl.token.instructions import (
        close_account,
        CloseAccountParams,
    )
    from spl.token.constants import WRAPPED_SOL_MINT
    from spl.token._layouts import ACCOUNT_LAYOUT

    # 1. 加载用户密钥
    payer = load_keypair('user.json')
    owner = payer.pubkey()

    # 2. 计算WSOL的ATA地址
    from spl.token.instructions import get_associated_token_address
    wsol_ata = get_associated_token_address(owner, WRAPPED_SOL_MINT)

    # 3. 检查ATA是否存在
    try:
        ata_info = client.get_account_info(wsol_ata)
        ata_exists = ata_info.value is not None
    except Exception:
        ata_exists = False

    instructions = []

    # 4. 如果ATA不存在，创建ATA
    if not ata_exists:
        instructions.append(
            create_associated_token_account_instruction(
                payer = payer.pubkey(),
                owner= payer.pubkey(),
                mint=WRAPPED_SOL_MINT
            )
        )

    # 5. 转账SOL到WSOL ATA（即存入SOL，获得等量WSOL）
    amount = int(1 * 1e9)  # 1 SOL
    instructions.append(
        transfer(
            TransferParams(
                from_pubkey=owner,
                to_pubkey=wsol_ata,
                lamports=amount
            )
        )
    )

    # 6. 构造并发送交易
    recent_blockhash = client.get_latest_blockhash().value.blockhash
    message = Message.new_with_blockhash(instructions, owner, recent_blockhash)
    tx = Transaction.new_unsigned(message)
    tx.sign([payer], recent_blockhash)
    print(get_solana_balance(owner, client=client))
    try:
        resp = client.send_transaction(tx, opts=TxOpts(preflight_commitment=Confirmed),)
        print("SOL 已成功 wrap 成 WSOL，交易签名:", resp.value)
        print(resp.to_json())
    except Exception as e:
        print("wrap SOL 失败:", e)

    confirmation = client.confirm_transaction(resp.value)
    print(confirmation.to_json())

    print(get_token_balance(wsol_ata, client=client))



def build_raydium_swap_cpmm_instruction(
    program_id: Pubkey,
    payer: Pubkey,
    authority: Pubkey,
    config_id: Pubkey,
    pool_id: Pubkey,
    user_input_account: Pubkey,
    user_output_account: Pubkey,
    input_vault: Pubkey,
    output_vault: Pubkey,
    input_token_program: Pubkey,
    output_token_program: Pubkey,
    input_mint: Pubkey,
    output_mint: Pubkey,
    observation_id: Pubkey,
    amount_in: int,
    amount_out_min: int,
    anchor_data_buf: bytes
) -> Instruction:
    """
    构建 Raydium CPMM swap_base_in 指令（Python 版）

    参数说明同 typescript 版本
    anchor_data_buf: bytes, 头部指令数据（如 swapBaseInput 操作码等）
    """
    from solders.instruction import Instruction, AccountMeta

    # 构建账户列表
    accounts = [
        AccountMeta(pubkey=payer, is_signer=True, is_writable=False),
        AccountMeta(pubkey=authority, is_signer=False, is_writable=False),
        AccountMeta(pubkey=config_id, is_signer=False, is_writable=False),
        AccountMeta(pubkey=pool_id, is_signer=False, is_writable=True),
        AccountMeta(pubkey=user_input_account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=user_output_account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=input_vault, is_signer=False, is_writable=True),
        AccountMeta(pubkey=output_vault, is_signer=False, is_writable=True),
        AccountMeta(pubkey=input_token_program, is_signer=False, is_writable=False),
        AccountMeta(pubkey=output_token_program, is_signer=False, is_writable=False),
        AccountMeta(pubkey=input_mint, is_signer=False, is_writable=False),
        AccountMeta(pubkey=output_mint, is_signer=False, is_writable=False),
        AccountMeta(pubkey=observation_id, is_signer=False, is_writable=True),
    ]

    # 指令数据编码（amount_in, amount_out_min 都为u64小端）
    data = amount_in.to_bytes(8, "little") + amount_out_min.to_bytes(8, "little")
    # 拼接头部指令数据
    full_data = bytes(anchor_data_buf) + data

    return Instruction(
        program_id=program_id,
        accounts=accounts,
        data=full_data
    )
    

# 2️⃣ 构建 Swap 指令
def build_raydium_swap_instruction(
    payer: Keypair,
    amount_in: int,
    min_amount_out: int
) -> Instruction:
    accounts = [
        # Raydium AMM 要求的账户结构
        AccountMeta(pubkey=POOL_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=payer.pubkey(), is_signer=True, is_writable=True),
        AccountMeta(pubkey=USDC_MINT, is_signer=False, is_writable=False),
        AccountMeta(pubkey=RAY_MINT, is_signer=False, is_writable=False),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False)
    ]
    
    # 指令数据编码 (swap_base_in)
    data = bytes([0x0B])  # Raydium 的 swap 操作码
    data += amount_in.to_bytes(8, "little")
    data += min_amount_out.to_bytes(8, "little")
    
    return Instruction(
        program_id=RAYDIUM_PROGRAM_ID,
        accounts=accounts,
        data=data
    )

def load_keypair(keyfile_path:str):
    keyfile = os.path.expanduser(keyfile_path)
    if os.path.exists(keyfile):
        with open(keyfile) as f:
            secret = json.load(f)
        return Keypair.from_bytes(bytes(secret))
    raise Exception("请先生成Solana钱包密钥文件~/.config/solana/id.json")

# 3️⃣ 执行 Swap 交易
def perform_swap():
    payer = load_keypair('user.json')# 本地测试账户
    amount_in = 10_000_000  # 10 USDC (6 decimals)
    min_out = 1  # 最小输出量
    
    # 构建交易
    swap_ix = build_raydium_swap_cpmm_instruction(
        program_id=RAYDIUM_PROGRAM_ID,
        payer=payer.pubkey(),
        authority=payer.pubkey(),
        config_id=RAYDIUM_PROGRAM_ID,
        pool_id=POOL_ID,
        user_input_account=payer.pubkey(),
        user_output_account=payer.pubkey(),
        input_vault=payer.pubkey(),
        output_vault=payer.pubkey(),
        input_token_program=TOKEN_PROGRAM_ID,
        output_token_program=TOKEN_PROGRAM_ID,
        input_mint=WSOL_MINT,
        output_mint=USDC_MINT,
        observation_id=Pubkey.from_string(""),
        amount_in=amount_in,
        amount_out_min=min_out,
        anchor_data_buf=bytes([0x0B])
    )
    recent_blockhash = client.get_latest_blockhash().value.blockhash
    message = Message.new_with_blockhash([swap_ix], payer.pubkey(), recent_blockhash)
    txn = Transaction.new_unsigned(message=message)
    
    # 签名并发送
    txn.sign([payer], recent_blockhash=recent_blockhash)
    try:
        resp = client.send_transaction(txn, opts=TxOpts(preflight_commitment=Confirmed))
        print("交易已发送，签名:", resp.value)
        print(resp.to_json())
        confirmation = client.confirm_transaction(resp.value, commitment=Confirmed)
    except Exception as e:
        print("交易失败:", e)
    print(f"Swap submitted: {resp.value}")

if __name__ == "__main__":
    perform_swap()