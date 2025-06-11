from typing import Any, Callable, Optional
from openai import AsyncClient
from web3 import Web3
from demo.agent import Agent
from demo.llm import GeneralLLM
from demo.tools import Tool, CodeInterpreter
from pydantic import BaseModel, Field
from execute import sign_and_send_transaction
from eth_account.signers.local import LocalAccount


def convert_pydantic_to_tool_schema(model_class: BaseModel) -> dict:
    """将 Pydantic 模型转换为工具调用的 JSON Schema 格式"""
    schema = model_class.model_json_schema()
    
    def resolve_refs(obj, definitions):
        """递归解析 $ref 引用"""
        if isinstance(obj, dict):
            if '$ref' in obj:
                # 解析引用
                ref_key = obj['$ref'].split('/')[-1]
                if ref_key in definitions:
                    resolved = definitions[ref_key].copy()
                    # 递归解析嵌套引用·
                    return resolve_refs(resolved, definitions)
                return obj
            else:
                # 递归处理所有字段
                return {k: resolve_refs(v, definitions) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [resolve_refs(item, definitions) for item in obj]
        return obj
    
    # 获取定义和属性
    definitions = schema.get('$defs', {})
    properties = schema.get('properties', {})
    
    # 解析所有引用
    resolved_properties = resolve_refs(properties, definitions)
    
    return resolved_properties

class Tx(BaseModel):
    to: str = Field(description="The address of the contract to interact with")
    value: int = Field(description="The value of the transaction in wei")
    data: str = Field(description="The data of the transaction, hex encoded")

class ValidateInput(BaseModel):
    tx_list: list[Tx] = Field(description="The list of transactions to validate")

class ExecuteTxTool(Tool):
    name = "validate_tx_execution"
    description = "Validate the transaction by executing it"
    input_arguments = {
        "tx_list": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "The address of the contract to interact with"
                    },
                    "value": {
                        "type": "integer",
                        "description": "The value of the transaction in wei"
                    },
                    "data": {
                        "type": "string",
                        "description": "The data of the transaction, hex encoded"
                    }
                },
                "required": ["to", "value", "data"],
                "additionalProperties": False
            },
            "description": "The list of transactions to validate"
        }
    }

    required_arguments = ['tx_list']


    def __init__(self, account:LocalAccount, w3:Web3) -> None:
        super().__init__()
        self.account = account
        self.w3 = w3
    
    async def call_tool(self, arguments:dict) -> str:
        tx_list = arguments.get('tx_list', [])
        if not tx_list:
            return "No transaction provided"
        total_gas_used = 0
        for tx in tx_list:
            success, gas_used = sign_and_send_transaction(tx, self.account, self.w3)
            if not success:
                return "Transaction execution failed"
            total_gas_used += gas_used
        return f"Transaction executed successfully, total gas used: {total_gas_used}"


class GetBalancesTool(Tool):
    name = "get_balances"
    description = "get the balance of the account"
    input_arguments = {}

    required_arguments = []

    def __init__(self, get_balances:Callable) -> None:
        super().__init__()
        self.get_balances = get_balances

    async def call_tool(self, arguments:dict) -> str:
        return await self.get_balances()
INSTRUCTIONS_PROMPT = """You are a validator for a transaction execution. You will be given a list of transactions and you need to validate if they are executed successfully.

## How to validate
1. Check current balances by using the `get_balances` tool
2. Extract the transaction list from the agent output
3. Validate the transaction json by using the `validate_tx_execution` tool to execute the transaction
4. According to the task and evaluate criteria, identify whether the transactions generated are all correct. 
5. check current balanced by usign the `get_balances` tool to check current balance state satisfy the criteria and correct.

Your final answer should be "FINAL ANSWER: PASS" or "FINAL ANSWER: FAIL"

Task: {question}
"""



class EvaluateAgent(Agent):
    def __init__(self, llm:GeneralLLM, tools:dict[str, Tool], max_turns:int = 10, instructions_prompt:str = INSTRUCTIONS_PROMPT, w3:Optional[Web3] = None) -> None:
        super().__init__(llm=llm, tools=tools, max_turns=max_turns, instructions_prompt=instructions_prompt)
        self.w3 = w3

    async def run(self, question:str, session_id:str = None) -> tuple[str, dict]:
        await self.reset_anvil()
        return await super().run(question, session_id)
    
    async def reset_anvil(self):
        ...
        # self.w3.provider.make_request(
        #     "anvil_reset",
        #     []
        # )



async def get_evaluate_agent(model_name:str, parameters:dict, account:LocalAccount, w3:Web3, get_balances:Callable, *args, **kwargs) -> Agent:
    max_turns = parameters.get("max_turns", 10)
    selected_tools = {
        "validate_tx_execution": ExecuteTxTool(account=account, w3=w3),
        "get_balances": GetBalancesTool(get_balances=get_balances)
    }
    llm = GeneralLLM(
        provider="openai",
        model_name=model_name,
        max_tokens=parameters.get("max_output_tokens", 16384),
        temperature=parameters.get("temperature", 0.0),
    )

    agent = EvaluateAgent(llm=llm, tools=selected_tools, max_turns=max_turns, instructions_prompt=INSTRUCTIONS_PROMPT, w3 = w3)
    return agent
    
    
