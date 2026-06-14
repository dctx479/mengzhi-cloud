# 环境配置与依赖管理
## Environment Setup & Dependency Management v1.0

**文档版本**: 1.0  
**创建日期**: 2026-06-11  
**适用范围**: 开发/测试/生产环境

---

## 一、开发环境快速搭建

### 1.1 系统要求

| 组件 | 最低版本 | 推荐版本 | 验证命令 |
|-----|---------|---------|---------|
| Python | 3.11 | 3.11 | `python --version` |
| Node.js | 18.x | 20.x | `node --version` |
| PostgreSQL | 14 | 15 | `psql --version` |
| Redis | 6 | 7 | `redis-server --version` |
| Docker | 20.x | 24.x | `docker --version` |
| Git | 2.30+ | 2.40+ | `git --version` |

### 1.2 一键安装脚本

**Windows (PowerShell)**:
```powershell
# scripts/setup_dev_env_windows.ps1

# 检查Chocolatey
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Chocolatey..."
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
}

# 安装依赖
choco install -y python311 nodejs-lts postgresql redis docker-desktop git

Write-Host "环境安装完成！请重启终端后运行 'python --version' 验证"
```

**macOS (Homebrew)**:
```bash
# scripts/setup_dev_env_macos.sh

#!/bin/bash

# 检查Homebrew
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 安装依赖
brew install python@3.11 node@20 postgresql@15 redis docker git

# 启动服务
brew services start postgresql@15
brew services start redis

echo "环境安装完成！运行 'python3 --version' 验证"
```

**Ubuntu/Debian**:
```bash
# scripts/setup_dev_env_ubuntu.sh

#!/bin/bash

sudo apt update

# Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# PostgreSQL 15
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update
sudo apt install -y postgresql-15

# Redis
sudo apt install -y redis-server

# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

echo "环境安装完成！"
```

---

## 二、后端环境配置

### 2.1 Python依赖管理（Poetry）

**安装Poetry**:
```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

**pyproject.toml**:
```toml
[tool.poetry]
name = "mengzhi-backend"
version = "1.0.0"
description = "蒙智云后端服务"
authors = ["Team <team@mengzhi.cloud>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
sqlalchemy = "^2.0.25"
alembic = "^1.13.0"
asyncpg = "^0.29.0"
redis = "^5.0.1"
anthropic = "^0.18.0"
pydantic = {extras = ["email"], version = "^2.5.0"}
pydantic-settings = "^2.1.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
python-multipart = "^0.0.6"
aiofiles = "^23.2.1"
minio = "^7.2.3"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
httpx = "^0.26.0"
black = "^23.12.0"
mypy = "^1.8.0"
pylint = "^3.0.0"
bandit = "^1.7.5"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**安装依赖**:
```bash
cd backend
poetry install  # 安装所有依赖
poetry install --no-dev  # 仅生产依赖
```

### 2.2 环境变量模板

**backend/.env.example**:
```bash
# 数据库配置
DATABASE_URL=postgresql://mengzhi:password@localhost:5432/mengzhi
DB_ECHO=False  # 是否打印SQL

# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# MinIO配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=mengzhi
MINIO_USE_SSL=False

# LLM配置
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_MODEL=claude-sonnet-4-20250514
ANTHROPIC_MAX_TOKENS=2000
ANTHROPIC_TIMEOUT=30

# JWT配置
SECRET_KEY=generate_with_openssl_rand_hex_32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
REFRESH_TOKEN_EXPIRE_DAYS=30

# 应用配置
APP_NAME=蒙智云
APP_VERSION=1.0.0
DEBUG=True
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:5173"]

# 速率限制
RATE_LIMIT_FREE_USER=100  # 免费用户每日配额
RATE_LIMIT_PAID_USER=1000

# 文件上传
MAX_FILE_SIZE_MB=10
ALLOWED_IMAGE_TYPES=["image/jpeg","image/png","image/webp"]
```

**生成密钥**:
```bash
# SECRET_KEY
openssl rand -hex 32

# 或使用Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2.3 数据库初始化

```bash
cd backend

# 创建数据库
createdb mengzhi

# 运行迁移
poetry run alembic upgrade head

# 初始化数据
poetry run python scripts/init_data.py

# 创建管理员
poetry run python scripts/create_admin.py
```

---

## 三、前端环境配置

### 3.1 Node.js依赖管理

**package.json**:
```json
{
  "name": "mengzhi-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "lint": "eslint . --ext .vue,.js,.ts,.jsx,.tsx --fix",
    "format": "prettier --write \"src/**/*.{js,ts,vue,css,scss}\"",
    "typecheck": "vue-tsc --noEmit"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "element-plus": "^2.5.0",
    "@element-plus/icons-vue": "^2.3.1",
    "axios": "^1.6.5",
    "dayjs": "^1.11.10"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "@vue/test-utils": "^2.4.3",
    "vite": "^5.0.0",
    "vitest": "^1.2.0",
    "typescript": "^5.3.0",
    "vue-tsc": "^1.8.27",
    "@typescript-eslint/eslint-plugin": "^6.18.0",
    "@typescript-eslint/parser": "^6.18.0",
    "eslint": "^8.56.0",
    "eslint-plugin-vue": "^9.19.0",
    "prettier": "^3.1.1",
    "sass": "^1.69.7"
  }
}
```

**安装依赖**:
```bash
cd frontend
npm install
```

### 3.2 环境变量模板

**frontend/.env.development**:
```bash
# API地址
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# MinIO地址
VITE_MINIO_ENDPOINT=http://localhost:9000

# 功能开关
VITE_ENABLE_MOCK=false
VITE_ENABLE_DEBUG=true
```

**frontend/.env.production**:
```bash
VITE_API_BASE_URL=https://api.mengzhi.cloud
VITE_API_TIMEOUT=30000
VITE_MINIO_ENDPOINT=https://cdn.mengzhi.cloud
VITE_ENABLE_MOCK=false
VITE_ENABLE_DEBUG=false
```

### 3.3 TypeScript配置

**tsconfig.json**:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "moduleResolution": "node",
    "strict": true,
    "jsx": "preserve",
    "sourceMap": true,
    "resolveJsonModule": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "allowSyntheticDefaultImports": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    },
    "types": ["vite/client", "element-plus/global"]
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
  "exclude": ["node_modules", "dist"]
}
```

---

## 四、Docker开发环境

### 4.1 docker-compose.dev.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: mengzhi-postgres-dev
    environment:
      POSTGRES_DB: mengzhi
      POSTGRES_USER: mengzhi
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mengzhi"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: mengzhi-redis-dev
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  minio:
    image: minio/minio:latest
    container_name: mengzhi-minio-dev
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_dev_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

volumes:
  postgres_dev_data:
  redis_dev_data:
  minio_dev_data:
```

**启动开发环境**:
```bash
# 启动所有服务
docker-compose -f docker-compose.dev.yml up -d

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f

# 停止服务
docker-compose -f docker-compose.dev.yml down

# 停止并删除数据卷
docker-compose -f docker-compose.dev.yml down -v
```

---

## 五、IDE配置

### 5.1 VS Code配置

**.vscode/settings.json**:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestPath": "pytest",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[vue]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "eslint.validate": [
    "javascript",
    "javascriptreact",
    "typescript",
    "typescriptreact",
    "vue"
  ],
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/node_modules": true,
    "**/.venv": true
  }
}
```

**.vscode/extensions.json**:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "Vue.volar",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-azuretools.vscode-docker",
    "GitHub.copilot"
  ]
}
```

### 5.2 PyCharm配置

1. 打开 `Settings` → `Project` → `Python Interpreter`
2. 选择 Poetry 环境：`backend/.venv/bin/python`
3. 配置代码格式化：`Settings` → `Tools` → `Black`
4. 启用测试：`Settings` → `Tools` → `Python Integrated Tools` → Test runner: `pytest`

---

## 六、依赖版本锁定

### 6.1 后端依赖锁定

**poetry.lock** 自动生成，提交到Git

```bash
# 更新所有依赖到最新兼容版本
poetry update

# 仅更新特定依赖
poetry update fastapi

# 查看过期依赖
poetry show --outdated
```

### 6.2 前端依赖锁定

**package-lock.json** 自动生成，提交到Git

```bash
# 根据package-lock.json安装依赖（推荐）
npm ci

# 更新依赖
npm update

# 检查过期依赖
npm outdated
```

---

## 七、环境隔离

### 7.1 Python虚拟环境

```bash
cd backend

# 创建虚拟环境
python3.11 -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 退出虚拟环境
deactivate
```

### 7.2 Node.js版本管理（nvm）

```bash
# 安装nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# 安装Node.js 20
nvm install 20
nvm use 20

# 设置默认版本
nvm alias default 20

# 项目级版本锁定
echo "20" > .nvmrc
nvm use  # 自动使用.nvmrc指定的版本
```

---

## 八、常见问题排查

### 8.1 依赖安装失败

**问题**: `poetry install` 失败

**解决**:
```bash
# 清理缓存
poetry cache clear pypi --all

# 更新Poetry
poetry self update

# 指定源（国内）
poetry config repositories.tsinghua https://pypi.tuna.tsinghua.edu.cn/simple
poetry config pypi-mirror.url https://pypi.tuna.tsinghua.edu.cn/simple
```

**问题**: `npm install` 失败

**解决**:
```bash
# 清理缓存
npm cache clean --force

# 删除node_modules和package-lock.json
rm -rf node_modules package-lock.json

# 重新安装
npm install

# 使用淘宝镜像
npm config set registry https://registry.npmmirror.com
```

### 8.2 数据库连接失败

**问题**: `psycopg2` 连接PostgreSQL失败

**检查**:
```bash
# 1. 确认PostgreSQL运行
sudo systemctl status postgresql

# 2. 测试连接
psql -U mengzhi -d mengzhi -h localhost

# 3. 检查防火墙
sudo ufw status

# 4. 查看PostgreSQL日志
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### 8.3 端口占用

**问题**: 端口已被占用

**解决**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

---

## 九、持续集成环境

### 9.1 GitHub Actions环境变量

**.github/workflows/test.yml**:
```yaml
env:
  DATABASE_URL: postgresql://postgres:postgres@localhost:5432/mengzhi_test
  REDIS_URL: redis://localhost:6379/0
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  SECRET_KEY: ${{ secrets.SECRET_KEY }}
```

**配置Secrets**:
1. GitHub仓库 → Settings → Secrets and variables → Actions
2. 添加：`ANTHROPIC_API_KEY`, `SECRET_KEY`

---

## 十、环境切换最佳实践

### 10.1 环境隔离

```
开发环境 (local)
  ├─ 数据库: localhost:5432/mengzhi_dev
  ├─ Redis: localhost:6379/0
  └─ API Key: 测试账号

测试环境 (test)
  ├─ 数据库: localhost:5432/mengzhi_test
  ├─ Redis: localhost:6379/1
  └─ API Key: 测试账号

生产环境 (prod)
  ├─ 数据库: RDS/云数据库
  ├─ Redis: 云Redis
  └─ API Key: 生产账号（严格限流）
```

### 10.2 配置管理工具

```python
# backend/app/core/config.py

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 环境标识
    ENVIRONMENT: str = "development"  # development/test/production
    
    # 数据库
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # LLM
    ANTHROPIC_API_KEY: str
    
    class Config:
        env_file = f".env.{os.getenv('ENVIRONMENT', 'development')}"
        case_sensitive = True

settings = Settings()
```

---

**文档结束**

> 环境配置是项目启动的第一步，务必确保所有依赖版本一致。
