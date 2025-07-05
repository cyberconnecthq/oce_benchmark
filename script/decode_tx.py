import json
from typing import Dict, Any, Optional
from web3 import Web3
from eth_abi.abi import decode


def get_canonical_type(param_type: Dict[str, Any]) -> str:
    """
    获取参数的规范类型字符串，用于计算函数选择器
    
    Args:
        param_type: ABI中的参数类型定义
        
    Returns:
        str: 规范的类型字符串
    """
    if param_type['type'] == 'tuple':
        # 对于tuple类型，需要递归处理其组件
        component_types = []
        for component in param_type['components']:
            component_types.append(get_canonical_type(component))
        return f"({','.join(component_types)})"
    elif param_type['type'].endswith('[]'):
        # 处理数组类型
        base_type = param_type['type'][:-2]  # 移除 '[]'
        if base_type == 'tuple':
            # tuple数组
            component_types = []
            for component in param_type['components']:
                component_types.append(get_canonical_type(component))
            return f"({','.join(component_types)})[]"
        else:
            return param_type['type']
    else:
        # 基本类型
        return param_type['type']


def decode_tx_data(hex_data: str, abi_json: str|dict) -> Dict[str, Any]:
    """
    解码交易数据
    
    Args:
        hex_data (str): 交易的data字段（十六进制格式，如 '0x...'）
        abi_json (str): 合约ABI的JSON字符串
        
    Returns:
        Dict[str, Any]: 解码后的数据，包含函数名和参数
        
    Raises:
        ValueError: 当数据格式不正确或无法找到匹配的函数时
    """
    try:
        # 解析ABI JSON
        if isinstance(abi_json, str):
            abi = json.loads(abi_json)
        else:
            abi = abi_json
            
        # 确保hex_data是正确的格式
        if not hex_data.startswith('0x'):
            hex_data = '0x' + hex_data
            
        # 检查数据长度（至少需要4字节的函数选择器）
        if len(hex_data) < 10:  # '0x' + 8个字符（4字节）
            raise ValueError("数据太短，无法包含有效的函数选择器")
            
        # 提取函数选择器（前4字节）
        function_selector = hex_data[:10]
        
        # 提取参数数据
        params_data = hex_data[10:]
        
        # 在ABI中查找匹配的函数
        target_function = None
        for item in abi:
            if item.get('type') == 'function':
                # 计算函数签名的选择器
                param_types = []
                for input_param in item.get('inputs', []):
                    param_types.append(get_canonical_type(input_param))
                
                function_signature = f"{item['name']}({','.join(param_types)})"
                calculated_selector = '0x' + Web3.keccak(text=function_signature)[:4].hex()
                
                if calculated_selector == function_selector:
                    target_function = item
                    break
                    
        if target_function is None:
            return {
                'function_selector': function_selector,
                'function_name': 'unknown',
                'raw_data': hex_data,
                'error': f'未找到匹配的函数选择器: {function_selector}'
            }
            
        # 解码参数
        decoded_params = {}
        if target_function.get('inputs') and params_data:
            try:
                # 构建参数类型列表，使用规范类型
                param_types = []
                param_names = []
                for input_param in target_function['inputs']:
                    param_types.append(get_canonical_type(input_param))
                    param_names.append(input_param['name'])
                
                # 解码参数数据
                if param_types:
                    # 检查并修复奇数长度的十六进制字符串
                    if len(params_data) % 2 != 0:
                        print(f"警告: 参数数据长度为奇数 ({len(params_data)})，自动添加0补齐")
                        params_data += '0'
                    
                    decoded_values = decode(param_types, bytes.fromhex(params_data))
                    
                    # 将解码的值与参数名配对
                    for i, (name, value, input_param) in enumerate(zip(param_names, decoded_values, target_function['inputs'])):
                        formatted_value = format_decoded_value(value, input_param)
                        decoded_params[name or f'param_{i}'] = formatted_value
                            
            except Exception as e:
                decoded_params = {'decode_error': str(e)}
                
        return {
            'function_selector': function_selector,
            'function_name': target_function['name'],
            'function_signature': f"{target_function['name']}({','.join([input_param['type'] for input_param in target_function.get('inputs', [])])})",
            'parameters': decoded_params,
            'raw_data': hex_data
        }
        
    except json.JSONDecodeError:
        raise ValueError("无效的ABI JSON格式")
    except Exception as e:
        raise ValueError(f"解码过程中发生错误: {str(e)}")


def format_decoded_value(value: Any, param_definition: Dict[str, Any]) -> Any:
    """
    格式化解码后的值，使其更易读
    
    Args:
        value: 解码后的原始值
        param_definition: 参数定义
        
    Returns:
        Any: 格式化后的值
    """
    if isinstance(value, bytes):
        # 将bytes转换为hex字符串
        return '0x' + value.hex()
    elif param_definition['type'] == 'tuple' and isinstance(value, tuple):
        # 对于tuple类型，递归格式化其组件
        formatted_tuple = {}
        for i, (component_value, component_def) in enumerate(zip(value, param_definition['components'])):
            component_name = component_def['name'] or f'field_{i}'
            formatted_tuple[component_name] = format_decoded_value(component_value, component_def)
        return formatted_tuple
    elif param_definition['type'].endswith('[]') and isinstance(value, (list, tuple)):
        # 对于数组类型，格式化每个元素
        base_type = param_definition['type'][:-2]
        if base_type == 'tuple':
            # tuple数组
            formatted_array = []
            for item in value:
                formatted_item = {}
                for j, (component_value, component_def) in enumerate(zip(item, param_definition['components'])):
                    component_name = component_def['name'] or f'field_{j}'
                    formatted_item[component_name] = format_decoded_value(component_value, component_def)
                formatted_array.append(formatted_item)
            return formatted_array
        else:
            # 基本类型数组
            return [format_decoded_value(item, {'type': base_type, 'name': ''}) for item in value]
    else:
        # 基本类型直接返回
        return value


def decode_tx_data_simple(hex_data: str, abi_json: str) -> Optional[Dict[str, Any]]:
    """
    简化版本的解码函数，出错时返回None而不是抛出异常
    
    Args:
        hex_data (str): 交易的data字段
        abi_json (str): 合约ABI的JSON字符串
        
    Returns:
        Optional[Dict[str, Any]]: 解码后的数据，失败时返回None
    """
    try:
        return decode_tx_data(hex_data, abi_json)
    except Exception as e:
        print(f"解码失败: {e}")
        return None


# 使用示例
if __name__ == "__main__":
    with open('./abi/uniswap_v3_npm_abi.json', 'r') as f:
        uniswap_v3_router_abi = json.load(f)
        # print(uniswap_v3_router_abi)
        data = "0x219f5d1700000000000000000000000000000000000000000000000000000000000fa16e00000000000000000000000000000000000000000000000000000000000027100000000000000000000000000000000000000000000000000000039c5670940000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006877e3ff"
        print(decode_tx_data(data, uniswap_v3_router_abi))
    
