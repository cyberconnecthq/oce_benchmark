#!/bin/bash
# start.sh - 启动脚本

set -e

# 从环境变量获取配置，设置默认值
RPC_URL=${RPC_URL:-"https://rpc.ankr.com/eth/e1529327d27a49660f1b8b9e747aec94256fcd84c82bd3ae28ce178915e00017"}
FORK_BLOCK=${FORK_BLOCK:-"22636495"}
BALANCE=${BALANCE:-"1000"}
ANVIL_PORT=${ANVIL_PORT:-"8545"}
APP_PORT=${APP_PORT:-"8000"}

echo "🚀 启动OCE Benchmark服务..."

# 启动anvil (后台运行)
echo "📡 启动Anvil节点..."
anvil \
  --fork-url "$RPC_URL" \
  --fork-block-number "$FORK_BLOCK" \
  --balance "$BALANCE" \
  --host 0.0.0.0 \
  --port "$ANVIL_PORT" \
  --silent &
echo "Anvil 启动命令如下："
echo "anvil --fork-url \"$RPC_URL\" --fork-block-number \"$FORK_BLOCK\" --balance \"$BALANCE\" --host 0.0.0.0 --port \"$ANVIL_PORT\" --silent &"

ANVIL_PID=$!
echo "Anvil PID: $ANVIL_PID"

# 等待anvil启动 - 使用正确的RPC调用
echo "⏳ 等待Anvil节点准备就绪..."
anvil_ready=false

for i in {1..60}; do
    # 使用JSON-RPC调用检查anvil状态
    if curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
        http://localhost:$ANVIL_PORT >/dev/null 2>&1; then
        
        # 进一步验证能获取到区块信息
        block_result=$(curl -s -X POST \
            -H "Content-Type: application/json" \
            -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
            http://localhost:$ANVIL_PORT)
        
        if echo "$block_result" | grep -q "result"; then
            echo "✅ Anvil节点已就绪"
            echo "当前区块: $(echo "$block_result" | grep -o '"result":"[^"]*"' | cut -d'"' -f4)"
            anvil_ready=true
            break
        fi
    fi
    
    # 检查anvil进程是否还在运行
    if ! kill -0 $ANVIL_PID 2>/dev/null; then
        echo "❌ Anvil进程已退出"
        exit 1
    fi
    
    if [ $i -eq 60 ]; then
        echo "❌ Anvil节点启动超时 (60秒)"
        echo "尝试检查Anvil日志..."
        # 给一些调试信息
        ps aux | grep anvil || true
        netstat -tulpn | grep $ANVIL_PORT || true
        exit 1
    fi
    
    echo "等待中... ($i/60)"
    sleep 1
done

if [ "$anvil_ready" = false ]; then
    echo "❌ Anvil节点未能正常启动"
    exit 1
fi

# 启动应用
echo "🌐 启动OCE Benchmark API..."
exec python main.py

# 清理函数
cleanup() {
    echo "🛑 停止服务..."
    kill $ANVIL_PID 2>/dev/null || true
    exit 0
}

# 设置信号处理
trap cleanup SIGTERM SIGINT