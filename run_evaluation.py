import json
from evaluate_module.schemas import AgentOutputItem, QuestionData
from web3 import Web3, HTTPProvider
from dataset.constants import RPC_URL
from demo.get_agent import get_agent
from evaluator import get_eval_agent_by_task_id
from evaluate_module.oce_evaluator import OCEEvaluator
import csv

evaluator = OCEEvaluator(RPC_URL)

w3 = Web3(HTTPProvider(RPC_URL)) 

async def run_eval(agent_outputs:list[AgentOutputItem]):

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
                value = getattr(item, key, "")
                # 对于复杂类型（如result/metadata为dict或list），转为格式化的JSON字符串
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False, indent=2)
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

    import asyncio
    output = AgentOutputItem(
        task_id="a2d42815-a8c4-4132-8851-f266f6cc8056",
        question=None,
        answer="Agent output: ```json\n[\n  {\n    \"from\": \"0xFAafe5FcaC0E87D40017E44CD462398026a12230\",\n    \"to\": \"0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2\",\n    \"value\": 0,\n    \"gas\": 70000,\n    \"gasPrice\": 1736689524,\n    \"nonce\": 5481,\n    \"chainId\": 1,\n    \"data\": \"0x095ea7b30000000000000000000000007a250d5630b4cf539739df2c5dacb4c659f2488d0000000000000000000000000000000000000000000000000de0b6b3a7640000\"\n  },\n  {\n    \"from\": \"0xFAafe5FcaC0E87D40017E44CD462398026a12230\",\n    \"to\": \"0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D\",\n    \"value\": 0,\n    \"gas\": 500000,\n    \"gasPrice\": 1736689524,\n    \"nonce\": 5482,\n    \"chainId\": 1,\n    \"data\": \"0x38ed17390000000000000000000000000000000000000000000000000de0b6b3a7640000000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000faafe5fcac0e87d40017e44cd462398026a1223000000000000000000000000000000000000000000000000000000000685ce01d0000000000000000000000000000000000000000000000000000000000000002000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc200000000000000000000000095ad61b0a150d79219dcf64e1e6cc01f0b64c4ce\"\n  }\n]\n```\nThis is the list of transactions needed (approve WETH to router, then swap on Uniswap V2). Both `nonce`, `gas`, and hex encodings are calculated. Sign and send in this order to execute the swap.\nNow validate the answer TXs are correct, executable and result in the right balance change"
    )
    result = asyncio.run(run_eval([output]))
    print(result)

    # output_file = 'converted_agent_outputs/converted_results_test_20250626_gpt4_1_70.json'
    # with open(output_file, 'r') as f:
    #     agent_outputs = [AgentOutputItem(**item) for item in json.load(f)]

    # results = asyncio.run(run_eval(agent_outputs=agent_outputs))


    


