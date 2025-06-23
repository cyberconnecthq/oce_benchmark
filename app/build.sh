#!/bin/bash

# Docker 构建脚本，带重试机制
set -e

echo "开始构建 OCE Benchmark Docker 镜像..."

# 设置构建参数
IMAGE_NAME="oce-benchmark-app"
DOCKERFILE_PATH="app/Dockerfile"
MAX_RETRIES=3
RETRY_COUNT=0

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo "错误: Docker 未运行，请启动 Docker Desktop"
    exit 1
fi

# 构建函数
build_image() {
    echo "尝试构建镜像 (第 $((RETRY_COUNT + 1)) 次)..."
    
    # 使用buildkit并设置超时
    DOCKER_BUILDKIT=1 docker build \
        --network=host \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --progress=plain \
        -t "$IMAGE_NAME" \
        -f "$DOCKERFILE_PATH" \
        .
}

# 重试循环
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if build_image; then
        echo "✅ 镜像构建成功！"
        echo "镜像名称: $IMAGE_NAME"
        echo "运行命令: docker run -p 8000:8000 -p 8545:8545 $IMAGE_NAME"
        exit 0
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "⚠️  构建失败，30秒后重试..."
            sleep 30
        else
            echo "❌ 构建失败，已达到最大重试次数"
            echo ""
            echo "建议的解决方案："
            echo "1. 检查网络连接"
            echo "2. 尝试使用VPN或更换网络"
            echo "3. 配置Docker镜像源"
            echo "4. 手动运行: docker pull python:3.12-slim"
            exit 1
        fi
    fi
done 