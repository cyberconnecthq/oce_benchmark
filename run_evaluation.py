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

async def run_eval(agent_outputs:list[AgentOutputItem], save_file:bool = False):

    # 执行批量评估
    results = await evaluator.evaluate_batch(
        agent_outputs=agent_outputs
    )

    # 保存为CSV
    csv_file = "eval_results_parallel_20250702_205636_4-1.csv"
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
        if not save_file:
            return results
        with open(csv_file, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=wanted_keys)
            writer.writeheader()
            for row in processed_results:
                writer.writerow(row)
        print(f"评估结果已保存为 {csv_file}")

    return results



if __name__ == '__main__':

    import asyncio
    # output = AgentOutputItem(
    #     task_id="73caf323-7b49-40e4-b42e-147cb235eb8d",
    #     question=None,
    #     answer="Agent output: [\n  {\n    \"from\": \"0xFAafe5FcaC0E87D40017E44CD462398026a12230\",\n    \"to\": \"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48\",\n    \"value\": 0,\n    \"gas\": 100000,\n    \"gasPrice\": 29757341793,\n    \"nonce\": 5481,\n    \"chainId\": 1,\n    \"data\": \"0x095ea7b3000000000000000000000000d69fc6ea47385213ad2ffc22480f0b67f4c20eb10000000000000000000000000000000000000000000000000000000000989680\"\n  },\n  {\n    \"from\": \"0xFAafe5FcaC0E87D40017E44CD462398026a12230\",\n    \"to\": \"0xd69Fc6ea47385213AD2fFc22480F0B67F4c20eb1\",\n    \"value\": 0,\n    \"gas\": 400000,\n    \"gasPrice\": 29757341793,\n    \"nonce\": 5482,\n    \"chainId\": 1,\n    \"data\": \"0x2334227a000000000000000000000000faafe5fcac0e87d40017e44cd462398026a12230000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb4800000000000000000000000000000000000000000000000000000000009896800000000000000000000000000000000000000000000000000000000000002105000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000685d44fd00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000\"\n  }\n]\n\nThese are the correct, signable, and directly executable Ethereum legacy transactions to:\n1. Approve the Across bridge to spend your 10 USDC,\n2. Bridge 10 USDC from Ethereum to Base network via Across Protocol.\n\nYou must send them in the listed order. Nonces and calldata are real and calculated.\nNow validate the answer TXs are correct, executable and result in the right balance change",
    # )
    # result = asyncio.run(run_eval([output]))
    # print(result)

    output_file = 'converted_agent_outputs/converted_results_parallel_20250702_205636_4-1.json'
    with open(output_file, 'r') as f:
        agent_outputs = [AgentOutputItem(**item) for item in json.load(f)]

    results = asyncio.run(run_eval(agent_outputs=agent_outputs,save_file=True))


    


