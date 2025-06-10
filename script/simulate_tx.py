#!/usr/bin/env python3
"""
模拟执行交易的工具类
"""

import os, json
from decimal import Decimal
from web3 import Web3, HTTPProvider
from web3.types import TxParams
from eth_account.signers.local import LocalAccount

class TxSimulator:
    def __init__(self, rpc_url="http://127.0.0.1:8545"):
        """初始化模拟器"""
        self.w3 = Web3(HTTPProvider(rpc_url))
        print(f"连接到 {rpc_url}")
        
        # 使用anvil默认账户作为模拟账户
        self.account: LocalAccount = self.w3.eth.account.from_key(
            "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        )
        self.address = self.account.address
        
    def simulate_tx(self, tx_params: TxParams) -> dict:
        """
        模拟执行交易
        
        Args:
            tx_params: 交易参数
            
        Returns:
            dict: 包含交易执行结果的字典
        """
        try:
            # 补充必要的交易参数
            if "from" not in tx_params:
                tx_params["from"] = self.address
                
            if "chainId" not in tx_params:
                tx_params["chainId"] = self.w3.eth.chain_id
                
            if "nonce" not in tx_params:
                tx_params["nonce"] = self.w3.eth.get_transaction_count(self.address)
                
            # 如果没有指定gas,则估算
            if "gas" not in tx_params:
                tx_params["gas"] = self.w3.eth.estimate_gas(tx_params)

            tx_params.update({
                "nonce": self.w3.eth.get_transaction_count(self.address),
                "chainId": self.w3.eth.chain_id,
            }) 
            
            # 签名并发送交易
            signed = self.account.sign_transaction(tx_params)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            
            # 等待交易被打包
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "gas_used": receipt.gasUsed,
                "status": receipt.status,
                "logs": receipt.logs,
                "receipt": receipt
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
            
    def simulate_contract_call(self, contract_address: str, abi: list, func_name: str, *args, **kwargs) -> dict:
        """
        模拟调用合约函数
        
        Args:
            contract_address: 合约地址
            abi: 合约ABI
            func_name: 要调用的函数名
            *args: 函数参数
            **kwargs: 交易参数(value, gas等)
            
        Returns:
            dict: 包含调用结果的字典
        """
        try:
            contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(contract_address),
                abi=abi
            )
            
            # 构建交易
            func = getattr(contract.functions, func_name)
            tx = func(*args).build_transaction(kwargs)
            
            # 模拟执行
            return self.simulate_tx(tx)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
            
    def get_balance(self, address: str, token_address: str = None) -> Decimal:
        """
        获取账户余额
        
        Args:
            address: 要查询的地址
            token_address: 代币合约地址,为None时查询ETH余额
            
        Returns:
            Decimal: 余额
        """
        try:
            if token_address is None:
                # 查询ETH余额
                balance = self.w3.eth.get_balance(address)
                return Decimal(balance) / Decimal(10**18)
            else:
                # 查询代币余额
                abi = json.loads("""[
                    {"constant":true,"inputs":[{"name":"owner","type":"address"}],
                     "name":"balanceOf","outputs":[{"name":"","type":"uint256"}],
                     "stateMutability":"view","type":"function"}
                ]""")
                token = self.w3.eth.contract(
                    address=self.w3.to_checksum_address(token_address),
                    abi=abi
                )
                balance = token.functions.balanceOf(address).call()
                decimals = 18  # 默认18位小数
                return Decimal(balance) / Decimal(10**decimals)
                
        except Exception as e:
            print(f"获取余额失败: {e}")
            return Decimal("0")

if __name__ == "__main__":
    simulator = TxSimulator()
    tx = {'from': '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266', 'to': '0x70997970C51812dc3A010C7d01b50e0d17dc79C8', 'value': 10000000000000000000}
    result = simulator.simulate_tx(tx)
    print(result)