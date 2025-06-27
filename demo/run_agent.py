import argparse
import asyncio
import json
import os
from datetime import datetime

from demo.agent import agent_logger
from demo.get_agent import get_agent
from demo.tools import tool_logger
from tqdm.asyncio import tqdm
from pydantic import BaseModel


class InputQuestion(BaseModel):
    question:str
    task_id:str

from schemas import QuestionData
from web3 import Web3, HTTPProvider
from dataset.constants import RPC_URL

w3 = Web3(HTTPProvider(RPC_URL)) 



async def run_tests_parallel(
    output_dir,
    questions:list[QuestionData]=[],
    model_name="anthropic/claude-3-7-sonnet-20250219",
    max_concurrent=5,
    save_results=False,
    parameters={},
):
    """Run multiple questions in parallel using the custom model"""
    agent = await get_agent(model_name, parameters)

    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_question(question):
        async with semaphore:
            return await agent.run(question)

    tasks = [process_question(question.question) for question in questions]

    results = await tqdm.gather(*tasks, desc="Processing questions")

    formatted_results = []
    for i, (question, result) in enumerate(zip(questions, results)):
        if isinstance(result, Exception):
            formatted_results.append(
                {"question": question.question, "task_id": question.task_id, "level": question.level, "category": question.category, "success": False, "error": str(result)}
            )
        else:
            formatted_results.append(
                {"question": question.question, "task_id": question.task_id, "level": question.level, "category": question.category, "success": True, "result": result}
            )

    if save_results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"results_test_{timestamp}.json")

        with open(output_file, "w") as f:
            json.dump(formatted_results, f, indent=2)

    return formatted_results

async def run_tests(
    output_dir,
    questions:list[QuestionData]=[],
    model_name="anthropic/claude-3-7-sonnet-20250219",
    save_results=False,
    parameters={},
):
    snapshot_id = w3.provider.make_request("evm_snapshot", [])["result"] # type: ignore
    formatted_results = []
    for question in questions:
        agent = await get_agent(model_name=model_name, parameters = parameters)
        #reset anvil environment
        w3.provider.make_request("evm_revert", [snapshot_id]) # type: ignore
        print("anvil reset")
        result = await agent.run(
            question = question.to_question(),
        )
        if isinstance(result, Exception):
            formatted_results.append(
                {"question": question.question, "task_id": question.task_id, "level": question.level, "category": question.category, "success": False, "error": str(result)}
            )
        else:
            formatted_results.append(
                {"question": question.question, "task_id": question.task_id, "level": question.level, "category": question.category, "success": True, "result": result}
            )

    if save_results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"results_test_{timestamp}.json")

        with open(output_file, "w") as f:
            json.dump(formatted_results, f, indent=2)

    return formatted_results

async def run_tests_parallel_with_reset(
    output_dir,
    questions: list[QuestionData] = [],
    model_name="anthropic/claude-3-7-sonnet-20250219",
    max_concurrent=10,
    save_results=False,
    parameters={},
):
    """Run multiple questions in parallel with individual environment resets"""
    
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_question(question):
        async with semaphore:
            try:
                # 为每个任务创建独立的agent实例
                agent = await get_agent(model_name=model_name, parameters=parameters)
                
                # 创建独立的snapshot并重置环境
                # snapshot_id = w3.provider.make_request("evm_snapshot", [])["result"] # type: ignore
                # w3.provider.make_request("evm_revert", [snapshot_id]) # type: ignore
                
                # 运行agent
                result = await agent.run(question=question.to_question())
                
                return result
            except Exception as e:
                return e

    tasks = [process_question(question) for question in questions]

    results = await tqdm.gather(*tasks, desc="Processing questions")

    formatted_results = []
    for i, (question, result) in enumerate(zip(questions, results)):
        if isinstance(result, Exception):
            formatted_results.append(
                {
                    "question": question.question,
                    "task_id": question.task_id,
                    "level": question.level,
                    "category": question.category,
                    "success": False,
                    "error": str(result),
                }
            )
        else:
            formatted_results.append(
                {
                    "question": question.question,
                    "task_id": question.task_id,
                    "level": question.level,
                    "category": question.category,
                    "success": True,
                    "result": result,
                }
            )

    if save_results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"results_parallel_{timestamp}.json")

        with open(output_file, "w") as f:
            json.dump(formatted_results, f, indent=2)

    return formatted_results


        



if __name__ == "__main__":
    import asyncio
    import json
    import os

    # 加载问题数据
    with open("dataset/oce_eval_data.json", "r") as f:
        questions_data = json.load(f)
    
    questions = [QuestionData(**item) for item in questions_data]
    # 提取所有问题
    # result = asyncio.run(run_tests_parallel(
    #     output_dir="results",
    #     questions=questions,
    #     model_name="volcengine/deepseek-r1-250120",
    #     max_concurrent=5,
    #     save_results=True,
    # ))
    # result = asyncio.run(run_tests_parallel(
    #     output_dir="results",
    #     questions=questions,
    #     model_name="openrouter/anthropic/claude-opus-4",
    #     max_concurrent=5,
    #     save_results=True,
    # ))

    # result = asyncio.run(run_tests_parallel(
    #     output_dir="results",
    #     questions=[QuestionData(task_id="123", question=question, level = 1, category='test')],
    #     model_name="anthropic/claude-sonnet-4-20250514",
    #     max_concurrent=5,
    #     save_results=True,
    # ))
    
    # 使用新的并行版本（带环境重置）
    # result = asyncio.run(run_tests_parallel_with_reset(
    #     output_dir="results",
    #     questions=questions[:10],  # 测试前10个问题
    #     model_name="openai/gpt-4.1",
    #     max_concurrent=3,  # 控制并发数量
    #     save_results=True,
    #     parameters={"max_turns": 25}
    # ))
    
    result = asyncio.run(run_tests_parallel_with_reset(
        output_dir="results",
        questions=questions,
        model_name="openai/o3-2025-04-16",
        save_results=True,
        parameters={"max_turns":25}
    ))
    

