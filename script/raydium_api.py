import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urljoin

# 常量声明
class API_URLS:
    POOL_KEY_BY_ID = "https://api-v3.raydium.io/pools/key/ids"
    BASE_URL = "https://api-v3.raydium.io"

# 数据结构定义
@dataclass
class PoolKeys:
    id: str
    programId: str
    mintA: Dict[str, Any]
    mintB: Dict[str, Any]
    vault: Dict[str, str]
    authority: str
    config: Dict[str, Any]
    observationId: str
    lookupTableAccount: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoolKeys':
        return cls(
            id=data.get('id', ''),
            programId=data.get('programId', ''),
            mintA=data.get('mintA', {}),
            mintB=data.get('mintB', {}),
            vault=data.get('vault', {}),
            authority=data.get('authority', ''),
            config=data.get('config', {}),
            observationId=data.get('observationId', ''),
            lookupTableAccount=data.get('lookupTableAccount')
        )

class RaydiumAPI:
    def __init__(self, base_url: str = API_URLS.BASE_URL, url_configs: Optional[Dict[str, str]] = None):
        self.base_url = base_url
        self.url_configs = url_configs or {}
        self.session = requests.Session()
        
        # 设置默认请求头
        self.session.headers.update({
            'User-Agent': 'RaydiumSDK-Python/1.0',
            'Content-Type': 'application/json'
        })
        
        # 池子键值缓存
        self.pool_keys_cache: Dict[str, PoolKeys] = {}
    
    async def fetch_pool_keys_by_id(self, id_list: List[str]) -> List[PoolKeys]:
        """
        根据池子ID列表获取池子键值信息
        
        Args:
            id_list: 池子ID列表
            
        Returns:
            PoolKeys对象列表
            
        Raises:
            requests.RequestException: API请求失败时抛出
        """
        cache_list: List[PoolKeys] = []
        
        # 过滤出未缓存的ID
        ready_list = []
        for pool_id in id_list:
            if pool_id in self.pool_keys_cache:
                cache_list.append(self.pool_keys_cache[pool_id])
            else:
                ready_list.append(pool_id)
        
        data: List[PoolKeys] = []
        
        # 如果有未缓存的ID，发送API请求
        if ready_list:
            try:
                # 构建API URL
                api_url = self.url_configs.get('POOL_KEY_BY_ID', API_URLS.POOL_KEY_BY_ID)
                url = f"{api_url}?ids={','.join(ready_list)}"
                
                # 发送GET请求
                response = self.session.get(url, timeout=30)
                response.raise_for_status()  # 抛出HTTP错误
                
                # 解析响应数据
                json_data = response.json()
                
                # 处理响应数据
                if isinstance(json_data, dict) and 'data' in json_data:
                    raw_data = json_data['data']
                elif isinstance(json_data, list):
                    raw_data = json_data
                else:
                    raw_data = []
                
                # 转换为PoolKeys对象并过滤空值
                data = [
                    PoolKeys.from_dict(item) 
                    for item in raw_data 
                    if item is not None
                ]
                
                # 将新数据加入缓存
                for pool_key in data:
                    if pool_key.id:
                        self.pool_keys_cache[pool_key.id] = pool_key
                        
            except requests.RequestException as e:
                print(f"API请求失败: {e}")
                raise
            except (ValueError, KeyError) as e:
                print(f"数据解析失败: {e}")
                raise
        
        # 返回缓存数据和新数据的合并
        return cache_list + data
    
    def clear_cache(self):
        """清空缓存"""
        self.pool_keys_cache.clear()
    
    def get_cache_size(self) -> int:
        """获取缓存大小"""
        return len(self.pool_keys_cache)

# 使用示例
async def main():
    """使用示例"""
    # 初始化API客户端
    api = RaydiumAPI()
    
    
    try:
        # 获取池子键值信息
        pool_ids = [
            "3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv",
        ]
        
        pool_keys = await api.fetch_pool_keys_by_id(pool_ids)
        
        print(f"获取到 {len(pool_keys)} 个池子信息:")
        for pool_key in pool_keys:
            print(f"池子ID: {pool_key.id}")
            print(f"程序ID: {pool_key.programId}")
            print(f"MintA: {pool_key.mintA}")
            print(f"MintB: {pool_key.mintB}")
            print("---")
            
        print(f"缓存大小: {api.get_cache_size()}")
        
    except Exception as e:
        print(f"错误: {e}")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())