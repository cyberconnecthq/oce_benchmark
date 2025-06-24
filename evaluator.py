import json
import asyncio
from statistics import mean
from typing import List
from demo.agent import Agent
from schemas import AgentOutputItem, Answer, BenchmarkItem, EvaluateScore
from evaluate_module.validate_agent import get_evaluate_agent


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
    evaluate_dataset = asyncio.run(load_evaluate_data("dataset/oce_eval_data.json"))
    print(evaluate_dataset)
    task_id = "60d4b5fb-0a04-49fb-bd16-7ad56cfc0b1d"
    account, w3, get_balances = load_task_dependencies(task_id)
    print(account, w3, get_balances)

    agent_output_item = AgentOutputItem(
        task_id=task_id,
        answer="```json\n[{\n    \"from\": \"0xFAafe5FcaC0E87D40017E44CD462398026a12230\",\n    \"to\": \"0xae7ab96520de3a18e5e111b5eaab095312d7fe84\",\n    \"value\": 500000000000000000,\n    \"gas\": 200000,\n    \"gasPrice\": 150000000000,\n    \"nonce\": 5949,\n    \"data\": \"0xa1903eab0000000000000000000000000000000000000000000000000000000000000000\",\n    \"chainId\": 1\n}]\n```\nThis transaction stakes 0.5 ETH to Lido on Ethereum mainnet with the correct calldata for `submit(address)` (referral: 0x0), ready to be signed and sent.",
    )

    # asyncio.run(run_evaluate(agent_output_item))
    eval_agent = asyncio.run(get_eval_agent_by_task_id(task_id))
    asyncio.run(eval_agent.run(agent_output_item.to_question()))