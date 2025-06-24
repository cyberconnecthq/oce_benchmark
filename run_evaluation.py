import json
from schemas import AgentOutputItem, QuestionData
from web3 import Web3, HTTPProvider
from dataset.constants import RPC_URL
from demo.get_agent import get_agent
from evaluator import get_eval_agent_by_task_id

w3 = Web3(HTTPProvider(RPC_URL)) 

async def run_eval(agent_outputs:list[AgentOutputItem],questions:list[QuestionData]):
    snapshot_id = w3.provider.make_request("evm_snapshot", [])["result"]
    results = []
    for output in agent_outputs:
        w3.provider.make_request("evm_revert", [snapshot_id])
        print("anvil已重置")
    return results
    for question in questions:
        ...



if __name__ == '__main__':
    with open("dataset/oce_eval_data.json", "r") as f:
        questions_data = json.load(f)
    
    questions = [QuestionData(**item) for item in questions_data]


