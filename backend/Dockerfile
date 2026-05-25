# 后端Dockerfile - Python FastAPI

FROM python:3.11-slim-bullseye

WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=300

# 换用阿里云 Debian 镜像源，安装系统依赖
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖（使用清华镜像源加速，信任该源）
RUN pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    --timeout=300 \
    -r requirements.txt

# 预装 LangChain（客服 Agent + MCP 工具）
# 使用兼容版本范围，避免 langgraph 循环依赖问题
RUN pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    --timeout=300 \
    "langchain>=0.1.0,<0.3.0" \
    "langchain-core>=0.1.0,<0.3.0" \
    "langchain-openai>=0.1.0,<0.3.0" \
    "bcrypt>=4.0.0,<5.0.0"

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs uploads

# 暴露端口
EXPOSE 8000

# 健康检查（使用内置urllib，不依赖requests）
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

# 启动应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
