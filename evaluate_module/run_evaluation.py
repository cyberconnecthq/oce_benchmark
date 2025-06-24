import asyncio
import json
from typing import Any, Dict
from evaluate_module.schemas import AgentOutputItem, QuestionData
from web3 import Web3, HTTPProvider
from dataset.constants import RPC_URL
from demo.get_agent import get_agent
from evaluator import get_eval_agent_by_task_id
from evaluate_module.oce_evaluator import OCEEvaluator

w3 = Web3(HTTPProvider(RPC_URL)) 
# 便捷函数
async def quick_evaluate(
    task_id: str,
    answer: str,
    model_name: str = "gpt-4.1"
) -> Dict[str, Any]:
    """快速评估单个任务"""
    evaluator = OCEEvaluator()
    agent_output = AgentOutputItem(
        task_id=task_id,
        answer=answer,
    )
    return await evaluator.evaluate_single(agent_output, model_name)

async def run_eval(agent_outputs:list[AgentOutputItem]):
    results = []
    for output in agent_outputs:
        result = await quick_evaluate(output.task_id, output.answer) if output.task_id else None
        results.append(result)
    return results


# if __name__ == '__main__':
    # asyncio.run(run_eval(agent_outputs))
    


