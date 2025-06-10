import json
import asyncio
from statistics import mean
from typing import List
from demo.agent import Agent
from schemas import AgentOutputItem, Answer, BenchmarkItem, EvaluateScore
from validate_agent import get_evaluate_agent


def load_llm_config(config_path:str = "llm_config.json") -> dict:
    with open(config_path, "r") as f:
        return json.load(f)

def load_agent_output_dataset(dataset_path:str = "dataset/example_agent_output.json") -> list[AgentOutputItem]:
    with open(dataset_path, "r") as f:
        agent_output_dataset = json.load(f)
        return [AgentOutputItem(**item) for item in agent_output_dataset]


async def get_eval_agent_by_task_id(task_id:str, model_name:str = 'gpt-4.1') -> Agent:
    account, w3, get_balances = load_task_dependencies(task_id)
    if account is None or w3 is None or get_balances is None:
        raise ValueError(f"Task {task_id} init failed")
    eval_agent = await get_evaluate_agent(
        model_name=model_name,
        parameters={
            "max_turns": 10,
            "max_output_tokens": 16384,
            "temperature": 0.0
        },
        account=account,
        w3=w3,
        get_balances=get_balances,
    )
    return eval_agent


async def load_evaluate_data(eval_dataset_path:str) -> List[BenchmarkItem]:
    with open(eval_dataset_path, "r") as f:
        content = json.load(f)
        benchmark_items = []
        for item in content:
            benchmark_item = BenchmarkItem(**item)
            benchmark_items.append(benchmark_item)
        return benchmark_items


def load_task_dependencies(task_id: str):
    """
    Dynamically load dependencies for the specified task
    
    Args:
        task_id: Task ID
        
    Returns:
        tuple: (account, w3, get_balances) or (None, None, None) if failed
    """
    import importlib
    
    try:
        module_name = f"dataset.tasks.{task_id}.validate"
        module = importlib.import_module(module_name)
        
        # Check if required attributes exist
        required_attrs = ['account', 'w3', 'get_balances']
        for attr in required_attrs:
            if not hasattr(module, attr):
                raise AttributeError(f"Module {module_name} missing attribute {attr}")
        
        return module.account, module.w3, module.get_balances
        
    except ImportError as e:
        print(f"Import error: {e}")
        return None, None, None
    except AttributeError as e:
        print(f"Attribute error: {e}")
        return None, None, None
    except Exception as e:
        print(f"Unknown error: {e}")
        return None, None, None

if __name__ == "__main__":
    task_id = "123e4567-e89b-12d3-a456-426614174000"
    account, w3, get_balances = load_task_dependencies(task_id)
    print(account, w3, get_balances)
    import asyncio
    ans = [
        {
            "to": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "value": 100000000000000000,
            "gas": 60000,
            "maxFeePerGas": 50000000000,
            "maxPriorityFeePerGas": 2000000000,
            "data": "0xd0e30db0",
            "chainId": 1
        },
        {
            "to": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "value": 0,
            "gas": 60000,
            "maxFeePerGas": 50000000000,
            "maxPriorityFeePerGas": 2000000000,
            "data": "0x095ea7b3000000000000000000000000E592427A0AEce92De3Edee1F18E0157C0586156400000000000000000000000000000000000000000000000DE0B6B3A7640000",
            "chainId": 1
        },
        {
            "to": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
            "value": 0,
            "gas": 300000,
            "maxFeePerGas": 50000000000,
            "maxPriorityFeePerGas": 2000000000,
            "data": "0x414bf389000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb4800000000000000000000000000000000000000000000000000000000000001f4000000000000000000000000f39fd6e51aad88f6f4ce6ab8827279cfffb92266000000000000000000000000000000000000000000000000000000006843b57e000000000000000000000000000000000000000000000000016345785d8a000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
            "chainId": 1
        }
    ]

    agent_output_item = AgentOutputItem(
        task_id=task_id,
        answer="Below is the ready-to-sign list of EIP-1559 (type-2) transactions that will:\n\n1. Wrap exactly 1 ETH into WETH  \n2. Approve the Uniswap V3 router to spend that 1 WETH  \n3. Swap the 1 WETH for USDC through Uniswap V3 (0.05 % / 500 bps pool)\n\nAll values (nonce, gas fees, calldata, etc.) were produced with live main-net data at block latest and are therefore directly executable.  \nSimply sign and send each TX in order.\n\n```json\n[\n  {\n    \"type\": 2,\n    \"nonce\": 5672,\n    \"to\": \"0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2\",\n    \"value\": 1000000000000000000,\n    \"data\": \"0xd0e30db0\",\n    \"gas\": 100000,\n    \"maxFeePerGas\": 3691473554,\n    \"maxPriorityFeePerGas\": 2000000000,\n    \"chainId\": 1\n  },\n  {\n    \"type\": 2,\n    \"nonce\": 5673,\n    \"to\": \"0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2\",\n    \"value\": 0,\n    \"data\": \"0x095ea7b3000000000000000000000000e592427a0aece92de3edee1f18e0157c058615640000000000000000000000000000000000000000000000000de0b6b3a7640000\",\n    \"gas\": 70000,\n    \"maxFeePerGas\": 3691473554,\n    \"maxPriorityFeePerGas\": 2000000000,\n    \"chainId\": 1\n  },\n  {\n    \"type\": 2,\n    \"nonce\": 5674,\n    \"to\": \"0xE592427A0AEce92De3Edee1F18E0157C05861564\",\n    \"value\": 0,\n    \"data\": \"0x414bf389000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb4800000000000000000000000000000000000000000000000000000000000001f4000000000000000000000000faafe5fcac0e87d40017e44cd462398026a122300000000000000000000000000000000000000000000000000000000068440d230000000000000000000000000000000000000000000000000de0b6b3a764000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000\",\n    \"gas\": 300000,\n    \"maxFeePerGas\": 3691473554,\n    \"maxPriorityFeePerGas\": 2000000000,\n    \"chainId\": 1\n  }\n]\n```\n\nExplanation of each step\n\u2022 TX-1 (nonce 5672) \u2013 WETH `deposit()`; sends 1 ETH, receives 1 WETH  \n\u2022 TX-2 (nonce 5673) \u2013 WETH `approve(router, 1 WETH)`  \n\u2022 TX-3 (nonce 5674) \u2013 Uniswap V3 `exactInputSingle` swapping 1 WETH \u2192 USDC, recipient = your wallet, deadline = now + 30 min, amountOutMinimum = 0 (set slippage as desired before signing if you want protection).\n\nSign these JSON objects with the private key of 0xFAafe5FcaC0E87D40017E44CD462398026a12230 and broadcast; the operations will execute sequentially.",
        tool_use_list=[],
        reasoning_list=[]
    )

    # asyncio.run(run_evaluate(agent_output_item))
    eval_agent = asyncio.run(get_eval_agent_by_task_id(task_id))
    asyncio.run(eval_agent.run(agent_output_item.to_question()))