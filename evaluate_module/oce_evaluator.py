# oce_evaluator.py - 核心评估库
from typing import Dict, Any
from evaluate_module.schemas import AgentOutputItem, BenchmarkItem
from evaluate_module.evaluator import get_eval_agent_by_task_id, load_evaluate_data
from web3 import Web3, HTTPProvider
from dataset.constants import RPC_URL

class OCEEvaluator:
    """轻量级OCE评估器"""
    
    def __init__(self, rpc_url: str = RPC_URL, evaluate_dataset_path:str = "dataset/oce_eval_data.json"):
        self.w3 = Web3(HTTPProvider(rpc_url))
        self._snapshots = {}
        self.evaluate_dataset: list[BenchmarkItem]=  []
        self.evaluate_dataset_path = evaluate_dataset_path
    
    async def load_eval_dataset(self, evaluate_dataset_path:str , force_reload:bool = False) -> list[BenchmarkItem]:
        if self.evaluate_dataset and not force_reload:
            return self.evaluate_dataset
        self.evaluate_dataset = await load_evaluate_data(evaluate_dataset_path)
        return self.evaluate_dataset
    
    async def evaluate_single(
        self, 
        agent_output: AgentOutputItem,
        model_name: str = "gpt-4.1"
    ) -> Dict[str, Any]:
        """评估单个任务"""
        try:
            await self.load_eval_dataset(self.evaluate_dataset_path)
            # 创建快照
            snapshot_id = self.w3.provider.make_request("evm_snapshot", []).get("result", "") # type: ignore

            if agent_output.task_id:
                task_id = agent_output.task_id
            elif agent_output.question:
                item = [item for item in self.evaluate_dataset if item.question == agent_output.question]
                if not item or len(item) <= 0:
                    return {
                        "task_id": agent_output.task_id,
                        "error": f"no evaluate data found for question : '{agent_output.question}'",
                        "status": "failed"
                    }
                task_id = item[0].task_id
            
            # 获取评估智能体
            eval_agent = await get_eval_agent_by_task_id(
                task_id, 
                model_name
            )
            
            # 执行评估
            result, metadata = await eval_agent.run(agent_output.to_question())
            
            # 解析结果
            score = self._parse_evaluation_result(result, agent_output)
            
            return {
                "task_id": agent_output.task_id,
                "score": score,
                "result": result,
                "metadata": metadata,
                "status": "success"
            }
            
        except Exception as e:
            print(e)
            return {
                "task_id": agent_output.task_id,
                "error": str(e),
                "status": "failed"
            }
        finally:
            # 恢复快照
            if snapshot_id:
                self.w3.provider.make_request("evm_revert", [snapshot_id]) # type: ignore
    
    async def evaluate_batch(
        self, 
        agent_outputs: list[AgentOutputItem],
        model_name: str = "gpt-4.1"
    ) -> list[Dict[str, Any]]:
        """批量评估"""
        results = []
        for output in agent_outputs:
            result = await self.evaluate_single(output, model_name)
            results.append(result)
        return results
    
    def _parse_evaluation_result(self, result: str, agent_output: AgentOutputItem) -> float:
        """解析评估结果为分数"""
        if "PASS" in result.upper():
            return 10.0
        else:
            return 0.0

