import json
import asyncio
from statistics import mean
from typing import List, Tuple, Optional, Any, Callable, Union
from types import ModuleType
from demo.agent import Agent
from evaluate_module.schemas import AgentOutputItem, BenchmarkItem 
from evaluate_module.validate_agent import get_evaluate_agent
from web3 import Web3


def load_llm_config(config_path:str = "llm_config.json") -> dict:
    with open(config_path, "r") as f:
        return json.load(f)

def load_agent_output_dataset(dataset_path:str = "dataset/example_agent_output.json") -> list[AgentOutputItem]:
    with open(dataset_path, "r") as f:
        agent_output_dataset = json.load(f)
        return [AgentOutputItem(**item) for item in agent_output_dataset]


async def get_eval_agent_by_task_id(task_id:str, model_name:str = 'gpt-4.1') -> Agent:
    account, w3, get_balances, pre_script = load_task_dependencies(task_id)
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
        pre_script=pre_script
    )
    return eval_agent


def load_evaluate_data(eval_dataset_path:str) -> list[BenchmarkItem]:
    with open(eval_dataset_path, "r") as f:
        content = json.load(f)
        benchmark_items = []
        for item in content:
            benchmark_item = BenchmarkItem(**item)
            benchmark_items.append(benchmark_item)
        return benchmark_items


def load_task_dependencies(task_id: str) -> Tuple[Optional[Any], Optional[Web3], Optional[Any], Optional[ModuleType]]:
    """
    Dynamically load dependencies for the specified task
    
    Args:
        task_id: Task ID
        
    Returns:
        tuple: (account, w3, get_balances, pre_script) or (None, None, None, None) if failed
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
        
        # Try to load pre_script module (optional)
        pre_script = None
        try:
            pre_script_module_name = f"dataset.tasks.{task_id}.pre_script"
            pre_script = importlib.import_module(pre_script_module_name)
            print(f"Successfully loaded pre_script for task {task_id}")
        except ImportError:
            print(f"No pre_script found for task {task_id}, skipping")
        except Exception as e:
            print(f"Error loading pre_script for task {task_id}: {e}")
        
        return module.account, module.w3, module.get_balances, pre_script
        
    except ImportError as e:
        print(f"Import error: {e}")
        return None, None, None, None
    except AttributeError as e:
        print(f"Attribute error: {e}")
        return None, None, None, None
    except Exception as e:
        print(f"Unknown error: {e}")
        return None, None, None, None

def execute_pre_script(pre_script: Optional[ModuleType]) -> bool:
    """
    执行pre_script模块，支持包含asyncio.run()的脚本
    
    Args:
        pre_script: pre_script模块对象
        
    Returns:
        bool: 执行是否成功
    """
    if not pre_script:
        print("未找到pre_script模块")
        return False
        
    print("正在运行 pre_script ...")
    
    def run_script():
        """执行脚本的内部函数"""
        if hasattr(pre_script, "run"):
            pre_script.run()
            return "run"
        elif hasattr(pre_script, "main"):
            pre_script.main()
            return "main"
        else:
            import importlib
            importlib.reload(pre_script)
            return "reload"
    
    try:
        import asyncio
        
        # 检查是否在事件循环中运行
        try:
            asyncio.get_running_loop()
            # 在事件循环中，使用独立线程执行避免冲突
            import threading
            
            result = None
            exception = None
            
            def thread_target():
                nonlocal result, exception
                try:
                    result = run_script()
                except Exception as e:
                    exception = e
            
            thread = threading.Thread(target=thread_target)
            thread.start()
            thread.join()
            
            if exception:
                raise exception
                
            print(f"pre_script.{result}() 在独立线程中运行完成。")
            return True
            
        except RuntimeError:
            # 没有运行的事件循环，直接执行
            result = run_script()
            print(f"pre_script.{result}() 运行完成。")
            return True
            
    except Exception as e:
        print(f"pre_script 运行出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    evaluate_dataset = asyncio.run(load_evaluate_data("dataset/oce_eval_data.json"))
    print(evaluate_dataset)
    task_id = "7c0be74e-2f8d-4fae-b900-4f790fa5cf12"
    account, w3, get_balances, pre_script = load_task_dependencies(task_id)
    print(account, w3, get_balances, pre_script)
    # 运行 pre_script，如果存在
    success = execute_pre_script(pre_script)

    agent_output_item = AgentOutputItem(
        task_id=task_id,
        answer="```json\n[{\n    \"from\": \"0xFAafe5FcaC0E87D40017E44CD462398026a12230\",\n    \"to\": \"0xae7ab96520de3a18e5e111b5eaab095312d7fe84\",\n    \"value\": 500000000000000000,\n    \"gas\": 200000,\n    \"gasPrice\": 150000000000,\n    \"nonce\": 5949,\n    \"data\": \"0xa1903eab0000000000000000000000000000000000000000000000000000000000000000\",\n    \"chainId\": 1\n}]\n```\nThis transaction stakes 0.5 ETH to Lido on Ethereum mainnet with the correct calldata for `submit(address)` (referral: 0x0), ready to be signed and sent.",
    )

    # asyncio.run(run_evaluate(agent_output_item))
    eval_agent = asyncio.run(get_eval_agent_by_task_id(task_id))
    asyncio.run(eval_agent.run(agent_output_item.to_question()))