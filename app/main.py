# app.py - 增强版API服务
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import asyncio
import os
import requests
from oce_evaluator import OCEEvaluator, quick_evaluate
from evaluate_module.schemas import AgentOutputItem
from typing import List
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OCE Evaluator", version="1.0.0")

# 从环境变量获取配置
ANVIL_URL = f"http://localhost:{os.getenv('ANVIL_PORT', '8545')}"
RPC_URL = os.getenv('RPC_URL', ANVIL_URL)

# 初始化评估器
evaluator = OCEEvaluator(rpc_url=RPC_URL)

@app.on_event("startup")
async def startup_event():
    """应用启动时的检查"""
    logger.info("🚀 OCE Evaluator 启动中...")
    
    # 检查anvil连接
    try:
        latest_block = evaluator.w3.eth.get_block('latest')
        logger.info(f"✅ Anvil连接成功，当前区块: {latest_block.number}") # type: ignore
    except Exception as e:
        logger.error(f"❌ Anvil连接失败: {e}")
        raise HTTPException(status_code=500, detail=f"Anvil连接失败: {e}")

@app.post("/evaluate")
async def evaluate_single(agent_output: AgentOutputItem, model_name: str = "gpt-4.1"):
    """单个任务评估"""
    logger.info(f"评估任务: {agent_output.task_id}")
    result = await evaluator.evaluate_single(agent_output, model_name)
    return result

@app.post("/evaluate/batch")
async def evaluate_batch(agent_outputs: List[AgentOutputItem], model_name: str = "gpt-4.1"):
    """批量评估"""
    logger.info(f"批量评估 {len(agent_outputs)} 个任务")
    results = await evaluator.evaluate_batch(agent_outputs, model_name)
    return {"results": results}

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查anvil连接
        latest_block = evaluator.w3.eth.get_block('latest')
        
        # 检查anvil RPC
        anvil_response = requests.get(ANVIL_URL, timeout=5)
        
        return {
            "status": "ok", 
            "block": latest_block.number, # type: ignore
            "anvil_url": ANVIL_URL,
            "anvil_status": "connected"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/anvil/info")
async def anvil_info():
    """获取anvil节点信息"""
    try:
        latest_block = evaluator.w3.eth.get_block('latest')
        network_info = evaluator.w3.eth.chain_id
        
        return {
            "chain_id": network_info,
            "latest_block": latest_block.number, # type: ignore
            "latest_block_hash": latest_block.hash.hex(), # type: ignore
            "anvil_url": ANVIL_URL
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/anvil/snapshot")
async def create_snapshot():
    """创建anvil快照"""
    try:
        snapshot_id = evaluator.w3.provider.make_request("evm_snapshot", []).get("result", None) # type: ignore
        if snapshot_id is None:
            raise HTTPException(status_code=500, detail="Failed to create snapshot")
        return {"snapshot_id": snapshot_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/anvil/revert/{snapshot_id}")
async def revert_snapshot(snapshot_id: str):
    """恢复到指定快照"""
    try:
        result = evaluator.w3.provider.make_request("evm_revert", [snapshot_id]) # type: ignore
        return {"success": result.get("result", False)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 快速启动
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('APP_PORT', '8000'))
    logger.info(f"启动应用在端口 {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")