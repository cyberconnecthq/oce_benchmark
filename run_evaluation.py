import json
from evaluate_module.schemas import AgentOutputItem, QuestionData
from web3 import Web3, HTTPProvider
from dataset.constants import RPC_URL
from demo.get_agent import get_agent
from evaluator import get_eval_agent_by_task_id
from evaluate_module.oce_evaluator import OCEEvaluator

evaluator = OCEEvaluator(RPC_URL)

w3 = Web3(HTTPProvider(RPC_URL)) 

async def run_eval(agent_outputs:list[AgentOutputItem]):
    import csv

    # 执行批量评估
    results = await evaluator.evaluate_batch(
        agent_outputs=agent_outputs
    )

    # 保存为CSV
    csv_file = "evaluation_results.csv"
    if results:
        # 只保留需要的字段，确保每一列单独列出来
        wanted_keys = ["task_id", "score", "result", "metadata", "status", "error"]
        processed_results = []
        for item in results:
            row = {}
            for key in wanted_keys:
                value = item.get(key, "")
                # 对于复杂类型（如result/metadata为dict或list），转为字符串
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                row[key] = value
            processed_results.append(row)

        with open(csv_file, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=wanted_keys)
            writer.writeheader()
            for row in processed_results:
                writer.writerow(row)
        print(f"评估结果已保存为 {csv_file}")

    return results



if __name__ == '__main__':
    output_file = 'converted_agent_outputs/converted_results_test_20250626_135111.json'
    with open(output_file, 'r') as f:
        agent_outputs = [AgentOutputItem(**item) for item in json.load(f)]

    import asyncio
    results = asyncio.run(run_eval(agent_outputs=agent_outputs[5:20]))
    


