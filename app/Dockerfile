# Dockerfile.fast - 使用官方Foundry镜像的快速版本
FROM ghcr.io/foundry-rs/foundry:latest AS foundry-source

# 主构建阶段
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    bash \
    git \
    && rm -rf /var/lib/apt/lists/*

# 从官方Foundry镜像复制预编译的二进制文件
COPY --from=foundry-source /usr/local/bin/forge /usr/local/bin/forge
COPY --from=foundry-source /usr/local/bin/cast /usr/local/bin/cast
COPY --from=foundry-source /usr/local/bin/anvil /usr/local/bin/anvil
COPY --from=foundry-source /usr/local/bin/chisel /usr/local/bin/chisel

# 验证Foundry安装
RUN forge --version && anvil --version

# 复制并安装Python依赖（在复制应用代码之前，以便更好地利用缓存）
COPY demo ./demo
COPY requirements.txt ./requirements.txt
COPY service_requirements.txt ./service_requirements.txt
RUN pip install --no-cache-dir -r service_requirements.txt

# 复制 evaluate_module 目录
COPY evaluate_module ./evaluate_module
COPY dataset ./dataset


# 复制应用代码
COPY app/ ./
COPY abi ./abi
# 设置启动脚本权限
RUN chmod +x /app/start.sh

# 健康检查 - 检查anvil和应用都在运行
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/health && curl -f http://localhost:8545 || exit 1

EXPOSE 8000 8545
CMD ["/app/start.sh"]