#!/usr/bin/env python3
"""
简化版 aggregatorId 查询示例
"""

import json
from pathlib import Path
from web3 import Web3

# 基本配置
RPC_URL = "http://127.0.0.1:8545"  # 替换为你的RPC URL
META_SWAP_CONTRACT_ADDRESS = "0x..."  # 替换为实际的MetaSwap合约地址

w3 = Web3(Web3.HTTPProvider(RPC_URL))

# 加载ABI
script_dir = Path(__file__).parent
abi_dir = script_dir.parent / "abi"
with open(abi_dir / "meta_swap_abi.json") as f:
    META_SWAP_ABI = json.load(f)

meta_swap = w3.eth.contract(
    address=Web3.to_checksum_address(META_SWAP_CONTRACT_ADDRESS),
    abi=META_SWAP_ABI
)

def query_aggregator_id(aggregator_id: str):
    """查询特定aggregatorId的信息"""
    try:
        # 1. 获取adapter信息
        adapter_info = meta_swap.functions.adapters(aggregator_id).call()
        addr, selector, data = adapter_info
        
        # 2. 检查是否被移除
        is_removed = meta_swap.functions.adapterRemoved(aggregator_id).call()
        
        print(f"\n📋 aggregatorId: {aggregator_id}")
        print(f"   合约地址: {addr}")
        print(f"   函数选择器: {selector.hex()}")
        print(f"   数据: {data.hex()}")
        print(f"   是否被移除: {is_removed}")
        print(f"   是否活跃: {addr != '0x0000000000000000000000000000000000000000' and not is_removed}")
        
        return True
    except Exception as e:
        print(f"❌ 查询 '{aggregator_id}' 失败: {e}")
        return False

def get_events_example():
    """获取最近事件的示例"""
    try:
        current_block = w3.eth.block_number
        start_block = max(0, current_block - 1000)  # 最近1000个区块
        
        # 获取AdapterSet事件
        adapter_set_filter = meta_swap.events.AdapterSet.create_filter(
            fromBlock=start_block,
            toBlock="latest"
        )
        
        events = adapter_set_filter.get_all_entries()
        print(f"\n📝 最近 {len(events)} 个 AdapterSet 事件:")
        
        for event in events:
            aggregator_id = event['args']['aggregatorId']
            print(f"   - {aggregator_id} (区块: {event['blockNumber']})")
        
        return [event['args']['aggregatorId'] for event in events]
        
    except Exception as e:
        print(f"❌ 获取事件失败: {e}")
        return []

if __name__ == "__main__":
    print("🔍 MetaSwap aggregatorId 查询示例")
    print("=" * 40)
    
    # 方法1: 查询常见的aggregatorId
    common_ids = ["uniswap_v3", "1inch", "paraswap", "0x", "curve"]
    
    print("\n📋 测试常见的aggregatorId:")
    for aggregator_id in common_ids:
        query_aggregator_id(aggregator_id)
    
    # 方法2: 从事件中获取
    print("\n📋 从事件中获取aggregatorId:")
    event_ids = get_events_example()
    
    # 查询从事件中获取的ID
    for aggregator_id in set(event_ids):  # 去重
        query_aggregator_id(aggregator_id) 