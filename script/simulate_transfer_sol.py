# 本脚本用于生成一笔1 SOL的转账交易
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.system_program import transfer, TransferParams
from solders.message import Message
import json
import os
from solana.rpc.commitment import Confirmed, Finalized
from solana.rpc.types import TxOpts

# 加载发送方密钥对
def load_keypair():
    keyfile = os.path.expanduser("~/.config/solana/id.json")
    if os.path.exists(keyfile):
        with open(keyfile) as f:
            secret = json.load(f)
        return Keypair.from_bytes(bytes(secret))
    raise Exception("请先生成Solana钱包密钥文件~/.config/solana/id.json")

# 设置节点和地址
client = Client("https://api.mainnet-beta.solana.com")
sender = load_keypair()
# sender_pub = sender.pubkey()
sender_pub = Pubkey.from_string("AgsYPSd9jQZEpbTMsvBWKdiAux3eyghdSY355QVHH9Hs")
# 请将下面的接收地址替换为目标地址
receiver_pub = Pubkey.from_string("DCyUzj7MhMoQzk2geWsaH5Rair4kBwZkpj1cAhxeoHWZ")

# 构造转账指令
tx_instruction = transfer(
    TransferParams(
        from_pubkey=sender_pub,
        to_pubkey=receiver_pub,
        lamports=int(0.5 * 1e9)  # 1 SOL = 1e9 lamports
    )
)
def get_balance(pubkey):
    try:
        balance_resp = client.get_balance(pubkey)
        balance = balance_resp.value / 1e9
        return balance
    except Exception as e:
        print("查询余额失败:", e)
        return False
# 获取最新区块哈希
recent_blockhash = client.get_latest_blockhash().value.blockhash

# 构造交易
message = Message.new_with_blockhash([tx_instruction], sender_pub, recent_blockhash)
tx = Transaction.new_unsigned(message)

# 签名交易
# tx.sign([sender], recent_blockhash)

print(get_balance(sender_pub))
print(get_balance(receiver_pub))
# 发送交易
try:
    resp = client.simulate_transaction(tx)
    print("交易已发送，签名:", resp.value)
    print(resp.to_json())
except Exception as e:
    print("交易失败:", e)

# client.confirm_transaction(resp.value, commitment=Finalized)
# print(get_balance(sender_pub))
# print(get_balance(receiver_pub))




