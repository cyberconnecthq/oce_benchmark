#!/usr/bin/env python3
"""
get_aggregator_ids.py - 获取 MetaSwap 合约的所有 aggregatorId 和对应的 aggregator 信息

通过以下方式获取 aggregatorId：
1. 监听 AdapterSet 事件获取所有已设置的 aggregatorId
2. 监听 AdapterRemoved 事件获取已移除的 aggregatorId
3. 查询特定 aggregatorId 的 adapter 详细信息
"""

import json
from pathlib import Path
from web3 import Web3
from dataset.constants import RPC_URL
from typing import List, Dict, Set

# 初始化 web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# MetaSwap 合约地址 (需要替换为实际地址)
META_SWAP_CONTRACT_ADDRESS = "0x..." # 请填入实际的 MetaSwap 合约地址

# 加载 ABI
script_dir = Path(__file__).parent
abi_dir = script_dir.parent / "abi"
with open(abi_dir / "meta_swap_abi.json") as f:
    META_SWAP_ABI = json.load(f)

# 获取合约实例
meta_swap = w3.eth.contract(
    address=Web3.to_checksum_address(META_SWAP_CONTRACT_ADDRESS), 
    abi=META_SWAP_ABI
)

def get_aggregator_ids_from_events(start_block: int = 0, end_block: str = "latest") -> Dict[str, Dict]:
    """
    通过监听事件日志获取所有 aggregatorId
    
    Args:
        start_block: 开始区块号
        end_block: 结束区块号 (可以是 "latest")
    
    Returns:
        Dict: {aggregatorId: {status: "active/removed", adapter_info: {...}}}
    """
    aggregators = {}
    
    print(f"🔍 扫描区块 {start_block} 到 {end_block} 的事件日志...")
    
    try:
        # 1. 获取 AdapterSet 事件 (新增/更新的 aggregator)
        adapter_set_filter = meta_swap.events.AdapterSet.create_filter(
            fromBlock=start_block,
            toBlock=end_block
        )
        
        set_events = adapter_set_filter.get_all_entries()
        print(f"📝 找到 {len(set_events)} 个 AdapterSet 事件")
        
        for event in set_events:
            aggregator_id = event['args']['aggregatorId']
            adapter_addr = event['args']['addr']
            selector = event['args']['selector']
            data = event['args']['data']
            
            aggregators[aggregator_id] = {
                'status': 'active',
                'address': adapter_addr,
                'selector': selector.hex(),
                'data': data.hex(),
                'block_number': event['blockNumber'],
                'tx_hash': event['transactionHash'].hex()
            }
        
        # 2. 获取 AdapterRemoved 事件 (已移除的 aggregator)
        adapter_removed_filter = meta_swap.events.AdapterRemoved.create_filter(
            fromBlock=start_block,
            toBlock=end_block
        )
        
        removed_events = adapter_removed_filter.get_all_entries()
        print(f"🗑️  找到 {len(removed_events)} 个 AdapterRemoved 事件")
        
        for event in removed_events:
            aggregator_id = event['args']['aggregatorId']
            
            if aggregator_id in aggregators:
                aggregators[aggregator_id]['status'] = 'removed'
                aggregators[aggregator_id]['removed_block'] = event['blockNumber']
                aggregators[aggregator_id]['removed_tx_hash'] = event['transactionHash'].hex()
            else:
                # 如果之前没有记录，说明这是一个在扫描范围外添加的adapter
                aggregators[aggregator_id] = {
                    'status': 'removed',
                    'removed_block': event['blockNumber'],
                    'removed_tx_hash': event['transactionHash'].hex()
                }
        
        return aggregators
        
    except Exception as e:
        print(f"❌ 获取事件日志时出错: {e}")
        return {}

def get_adapter_info(aggregator_id: str) -> Dict:
    """
    查询特定 aggregatorId 的 adapter 详细信息
    
    Args:
        aggregator_id: aggregator的ID
    
    Returns:
        Dict: adapter的详细信息
    """
    try:
        # 调用 adapters(string) 函数
        adapter_info = meta_swap.functions.adapters(aggregator_id).call()
        addr, selector, data = adapter_info
        
        # 检查是否已被移除
        is_removed = meta_swap.functions.adapterRemoved(aggregator_id).call()
        
        return {
            'address': addr,
            'selector': selector.hex(),
            'data': data.hex(),
            'is_removed': is_removed,
            'is_active': addr != "0x0000000000000000000000000000000000000000" and not is_removed
        }
    except Exception as e:
        print(f"❌ 查询 aggregatorId '{aggregator_id}' 信息时出错: {e}")
        return {}

def check_aggregator_id_exists(aggregator_id: str) -> bool:
    """
    检查 aggregatorId 是否存在
    
    Args:
        aggregator_id: aggregator的ID
    
    Returns:
        bool: True 如果存在且未被移除
    """
    try:
        adapter_info = meta_swap.functions.adapters(aggregator_id).call()
        addr, _, _ = adapter_info
        
        # 如果地址不是零地址，说明adapter存在
        if addr != "0x0000000000000000000000000000000000000000":
            # 再检查是否被标记为移除
            is_removed = meta_swap.functions.adapterRemoved(aggregator_id).call()
            return not is_removed
        
        return False
    except Exception:
        return False

def display_aggregators(aggregators: Dict[str, Dict]):
    """
    格式化显示 aggregator 信息
    """
    if not aggregators:
        print("❌ 没有找到任何 aggregator")
        return
    
    print(f"\n📋 发现 {len(aggregators)} 个 aggregator:")
    print("=" * 100)
    
    active_count = 0
    removed_count = 0
    
    for aggregator_id, info in aggregators.items():
        status = info.get('status', 'unknown')
        if status == 'active':
            active_count += 1
            print(f"✅ {aggregator_id}")
        else:
            removed_count += 1
            print(f"❌ {aggregator_id}")
        
        print(f"   状态: {status}")
        
        if 'address' in info:
            print(f"   合约地址: {info['address']}")
            print(f"   选择器: {info['selector']}")
            print(f"   数据: {info['data'][:20]}..." if len(info['data']) > 20 else f"   数据: {info['data']}")
            print(f"   设置区块: {info.get('block_number', 'N/A')}")
        
        if 'removed_block' in info:
            print(f"   移除区块: {info['removed_block']}")
        
        print("-" * 80)
    
    print(f"\n📊 统计: 活跃 {active_count} 个, 已移除 {removed_count} 个")

def get_common_aggregator_ids() -> List[str]:
    """
    返回一些常见的 aggregatorId 列表供测试
    (这些需要根据实际的合约配置来填写)
    """
    return [
        "uniswap_v2",
        "uniswap_v3", 
        "sushiswap",
        "curve",
        "balancer",
        "1inch",
        "paraswap",
        "0x_protocol"
    ]

def main():
    print("🚀 MetaSwap Aggregator ID 查询工具")
    print("=" * 50)
    
    # 检查合约连接
    try:
        # 尝试调用一个简单的view函数来测试连接
        owner = meta_swap.functions.owner().call()
        print(f"✅ 成功连接到 MetaSwap 合约")
        print(f"   合约地址: {META_SWAP_CONTRACT_ADDRESS}")
        print(f"   合约拥有者: {owner}")
    except Exception as e:
        print(f"❌ 无法连接到合约: {e}")
        print("   请检查:")
        print("   1. 合约地址是否正确")
        print("   2. RPC连接是否正常")
        print("   3. ABI文件是否正确")
        return
    
    # 方法1: 通过事件日志获取所有 aggregatorId
    print(f"\n📋 方法1: 通过事件日志获取 aggregatorId")
    current_block = w3.eth.block_number
    start_block = max(0, current_block - 100000)  # 扫描最近10万个区块
    
    aggregators = get_aggregator_ids_from_events(start_block)
    display_aggregators(aggregators)
    
    # 方法2: 测试常见的 aggregatorId
    print(f"\n📋 方法2: 测试常见的 aggregatorId")
    common_ids = get_common_aggregator_ids()
    
    print(f"🔍 测试 {len(common_ids)} 个常见的 aggregatorId...")
    for aggregator_id in common_ids:
        exists = check_aggregator_id_exists(aggregator_id)
        if exists:
            print(f"✅ {aggregator_id} - 存在")
            info = get_adapter_info(aggregator_id)
            if info:
                print(f"   地址: {info['address']}")
                print(f"   选择器: {info['selector']}")
        else:
            print(f"❌ {aggregator_id} - 不存在或已移除")
    
    # 方法3: 交互式查询
    print(f"\n📋 方法3: 交互式查询")
    print("输入 aggregatorId 来查询详细信息 (输入 'quit' 退出):")
    
    while True:
        try:
            user_input = input("\n请输入 aggregatorId: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input:
                continue
            
            print(f"🔍 查询 '{user_input}'...")
            info = get_adapter_info(user_input)
            
            if info and info.get('is_active'):
                print(f"✅ aggregatorId '{user_input}' 存在且活跃")
                print(f"   合约地址: {info['address']}")
                print(f"   选择器: {info['selector']}")
                print(f"   数据: {info['data']}")
            elif info and not info.get('is_active'):
                print(f"⚠️  aggregatorId '{user_input}' 存在但已被移除或未激活")
            else:
                print(f"❌ aggregatorId '{user_input}' 不存在")
                
        except KeyboardInterrupt:
            print(f"\n👋 程序被用户中断")
            break
        except Exception as e:
            print(f"❌ 查询出错: {e}")

if __name__ == "__main__":
    main() 